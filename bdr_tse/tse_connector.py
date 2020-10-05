from typing import Tuple
import enum

from bdr_tse.transport import (
    TransportCommand,
    Transport,
    TransportDataType,
    GetConfigDataID,
)


class TseConnector:
    def __init__(self, tse_path):
        self._transport = Transport(tse_path)

    def start(self):
        """Initializes the secure element and loads configuration data.

        :return: A dict containing:

            * ``version``: The version of the TSE.
            * ``serial``: The serial number of the TSE.
        """
        response = self._transport.send(TransportCommand.Start)
        return {
            "version": response[0].data,
            "serial": response[1].data,
        }

    def get_pin_status(self):
        """Returns the PIN/PUK transport states.

        Note that the value True means that the PIN is still in transport state. A
        fully-initialized TSE will return all as False.
        """
        response = self._transport.send(TransportCommand.GetPinStates)
        states = response[0].data
        return {
            "admin_pin_transport_state": bool(states[0]),
            "admin_puk_transport_state": bool(states[1]),
            "time_admin_pin_transport_state": bool(states[2]),
            "time_admin_puk_transport_state": bool(states[3]),
        }

    def initialize_pin_values(
        self,
        admin_puk: bytes,
        admin_pin: bytes,
        time_admin_puk: bytes,
        time_admin_pin: bytes,
    ):
        """Initialize TSE PIN values.

        :param admin_puk: The PUK to set for the Admin account. Must be exactly 10 bytes long.
        :param admin_pin: The PUK to set for the Admin account. Must be exactly 10 bytes long.
        :param time_admin_puk: The PUK to set for the TimeAdmin account. Must be exactly 8 bytes long.
        :param time_admin_pin: The PUK to set for the TimeAdmin account. Must be exactly 8 bytes long.

        """
        self._transport.send(
            TransportCommand.InitializePins,
            [
                (TransportDataType.BYTE_ARRAY, admin_puk),
                (TransportDataType.BYTE_ARRAY, admin_pin),
                (TransportDataType.BYTE_ARRAY, time_admin_puk),
                (TransportDataType.BYTE_ARRAY, time_admin_pin),
            ],
        )

    def factory_reset(self):
        """Resets the TSE to factory state.

        Note that this is only possible with TSE Engineering Samples.
        """
        # Magic factory reset procedure pulled from decompiled factory reset tool JAR
        self._transport.send(
            TransportCommand.FactoryReset,
            [(TransportDataType.BYTE_ARRAY, bytes([160, 0, 0, 1, 81, 83, 80, 65]))],
        )
        self._transport.send(
            TransportCommand.FactoryReset, [(TransportDataType.BYTE_ARRAY, bytes([0]))]
        )
        self._transport.send(
            TransportCommand.FactoryReset, [(TransportDataType.BYTE_ARRAY, bytes([0]))]
        )

    class AuthenticationResult(enum.IntEnum):
        SUCCESS = 0
        FAILED = 1
        PIN_BLOCKED = 2
        UNKNOWN_USER_ID = 3
        UNSPECIFIED_ERROR = 4

    class UserId(enum.Enum):
        ADMIN = "Admin"
        TIME_ADMIN = "TimeAdmin"

    def authenticate_user(self, user_id: UserId, pin: bytes):
        """Authenticate a user.

        :param user_id: The user ID of the user to authenticate.
        :param pin: The PIN to authenticate with.
        :return: A dictionary containing

            * ``authentication_result``: A :class:`TseConnector.AuthenticationResult`
            * ``remaining_retries``: The number of authentication retries left. Only
              relevant after having failed authentication.
        """
        response = self._transport.send(
            TransportCommand.AuthenticateUser,
            [
                (TransportDataType.STRING, user_id.value),
                (TransportDataType.BYTE_ARRAY, pin),
            ],
        )
        return {
            "authentication_result": TseConnector.AuthenticationResult(
                response[0].data
            ),
            "remaining_retries": response[1].data,
        }

    def unblock_user(self, user_id: UserId, puk: bytes, new_pin: bytes):
        """This command unblocks a user that has been blocked due to too much failed
        authentication attempts against the stored credentials (PIN). It
        authenticates using the PUK and sets new credentials (PIN).

        :param user_id: The user ID to unblock.
        :param puk; The PUK to authenticate with.
        :param new_pin: The new PIN to set for the user.
        :return: A ``TransportDataType.AuthenticationResult``
        """
        response = self._transport.send(
            TransportCommand.UnblockUser,
            [
                (TransportDataType.STRING, user_id.value),
                (TransportDataType.BYTE_ARRAY, puk),
                (TransportDataType.BYTE_ARRAY, new_pin),
            ],
        )
        return TseConnector.AuthenticationResult(response[0].data)

    def update_time(self, time_: int):
        """Update the system time of the TSE.

        :param time_: The time to set as a UNIX timestamp.
        """
        self._transport.send(
            TransportCommand.UpdateTime,
            [
                (TransportDataType.BYTE_ARRAY, time_.to_bytes(8, "big")),
            ],
        )

    def logout(self, user_id: UserId):
        """Log out an authenticated user."""
        self._transport.send(
            TransportCommand.Logout, [(TransportDataType.STRING, user_id.value)]
        )

    def initialize(self):
        """Initialize the TSE."""
        self._transport.send(TransportCommand.Initialize)

    def get_serial_number(self):
        """Get the key serial number from the TSE.

        A serial number is a hash value of a public key that belongs to a key pair
        whose private key is used to create signature values of log messages.

        Note that the API differs from the vendor-supplied API here. Since the TSE
        does not have the ability to generate new keys after initialization,
        there will only ever be one key. This function instead returns the serial
        number of this one key.
        """

        response = self._transport.send(TransportCommand.GetSerialNumbers)
        # This data is apparently ASN.1 encoded, but the examples supplied by the
        # vendor just use bytes [6:32+6] to avoid parsing it.
        return response[0].data[6 : 32 + 6]

    def start_transaction(
        self,
        client_id: str,
        process_data: bytes,
        process_type: str,
        additional_data: bytes = bytes(),
    ):
        """Opens a new transaction.

        :param client_id: The client ID.
        :param process_data: Process data for the transaction.
        :param process_type: Process type for the transaction.
        :param additional_data: Additional data for the transaction.

        :return: A dictionary containing

            * `transaction_number`: The identifying transaction number of the
              transaction, used in subsequent calls to
              :func:`~TseConnector.update_transaction` and
              :func:`~TseConnector.finish_transaction`.
            * `log_time`: The UNIX timestamp of the start of the transaction.
            * `signature_counter`: The signature counter.
            * `signature_value`: The signature value of the in-progress transaction.
            * `serial_number`: The serial number of the key that was used to sign.
        """
        response = self._transport.send(
            TransportCommand.StartTransaction,
            [
                (TransportDataType.STRING, client_id),
                (TransportDataType.BYTE_ARRAY, process_data),
                (TransportDataType.STRING, process_type),
                (TransportDataType.BYTE_ARRAY, additional_data),
            ],
        )
        return {
            "transaction_number": int.from_bytes(response[0].data, "big"),
            "signature_counter": int.from_bytes(response[1].data, "big"),
            "log_time": int.from_bytes(response[2].data, "big"),
            "signature_value": response[3].data,
            "serial_number": response[4].data,
        }

    def finish_transaction(
        self,
        transaction_number: int,
        client_id: str,
        process_data: bytes,
        process_type: str,
        additional_data: bytes,
    ):
        """Finishes a transaction.

        :param transaction_number: The transaction number to finish.
        :param client_id: The client ID.
        :param process_data: Process data for the transaction.
        :param process_type: Process type for the transaction.
        :param additional_data: Additional data for the transaction.

        :return: A dictionary with items identical to that returned in
            :func:`~TseConnector.start_transaction`.
        """
        response = self._transport.send(
            TransportCommand.FinishTransaction,
            [
                (TransportDataType.BYTE_ARRAY, transaction_number.to_bytes(4, "big")),
                (TransportDataType.STRING, client_id),
                (TransportDataType.BYTE_ARRAY, process_data),
                (TransportDataType.STRING, process_type),
                (TransportDataType.BYTE_ARRAY, additional_data),
            ],
        )
        return {
            "signature_counter": int.from_bytes(response[0].data, "big"),
            "log_time": int.from_bytes(response[1].data, "big"),
            "signature_value": response[2].data,
            "serial_number": response[3].data,
        }

    def map_ers_to_key(self, client_id: str, key_serial_number: bytes):
        """This command maps an ERS to a specific key.

        :param client_id: The client ID.
        :param key_serial_number: The key serial number.
        """
        self._transport.send(
            TransportCommand.MapERStoKey,
            [
                (TransportDataType.STRING, client_id),
                (TransportDataType.BYTE_ARRAY, key_serial_number),
            ],
        )

    def export_data(
        self,
        client_id: str = None,
        transaction_number: int = None,
        start_transaction_number: int = None,
        end_transaction_number: int = None,
        start_date: int = None,
        end_date: int = None,
        max_records: int = None,
    ):
        """Exports data from the TSE."""
        response = self._transport.send(
            TransportCommand.ExportData,
            [
                (TransportDataType.STRING, client_id or ""),
                (
                    TransportDataType.BYTE_ARRAY,
                    (transaction_number or 0xFFFFFFFF).to_bytes(4, "big"),
                ),
                (
                    TransportDataType.BYTE_ARRAY,
                    (start_transaction_number or 0x00000000).to_bytes(4, "big"),
                ),
                (
                    TransportDataType.BYTE_ARRAY,
                    (end_transaction_number or 0xFFFFFFFF).to_bytes(4, "big"),
                ),
                (
                    TransportDataType.BYTE_ARRAY,
                    (start_date or 0x0000000000000000).to_bytes(8, "big"),
                ),
                (
                    TransportDataType.BYTE_ARRAY,
                    (end_date or 0xFFFFFFFFFFFFFFFF).to_bytes(8, "big"),
                ),
                (
                    TransportDataType.BYTE_ARRAY,
                    (max_records or 0xFFFFFFFF).to_bytes(4, "big"),
                ),
            ],
        )
        return response

    def get_time_sync_interval(self) -> int:
        """Gets the required time sync interval in seconds."""
        response = self._transport.send(
            TransportCommand.GetConfigData,
            [(TransportDataType.SHORT, GetConfigDataID.TimeSyncInterval)],
        )
        return int.from_bytes(response[0].data, "big")
