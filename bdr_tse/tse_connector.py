from typing import Tuple
import struct
import enum

from bdr_tse.transport import TransportCommand, Transport, TransportDataType


class TseConnector:
    def __init__(self, tse_path):
        self._transport = Transport(tse_path)

    def start(self):
        response = self._transport.send(TransportCommand.Start)
        return {
            "version": response[0].data,
            "serial": response[1].data,
        }

    def get_pin_status(self) -> Tuple[bool, bool, bool, bool]:
        response = self._transport.send(TransportCommand.GetPinStates)
        states = response[0].data
        return list(bool(b) for b in states)

    def initialize_pin_values(
        self,
        admin_puk: bytes,
        admin_pin: bytes,
        time_admin_puk: bytes,
        time_admin_pin: bytes,
    ):
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
        # Magic factory reset procedure pulled from decompiled JAR
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
        response = self._transport.send(
            TransportCommand.UnblockUser,
            [
                (TransportDataType.STRING, user_id.value),
                (TransportDataType.BYTE_ARRAY, puk),
                (TransportDataType.BYTE_ARRAY, new_pin),
            ],
        )
        return TseConnector.AuthenticationResult(response[0].data)

    def update_time(self, time_):
        self._transport.send(
            TransportCommand.UpdateTime,
            [
                (TransportDataType.BYTE_ARRAY, struct.pack(">Q", time_)),
            ],
        )

    def initialize(self):
        self._transport.send(TransportCommand.Initialize, [])
