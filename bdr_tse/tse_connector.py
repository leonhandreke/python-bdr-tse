from typing import Tuple

from bdr_tse.transport import TransportCommand, Transport, TransportDataType

class TseConnector:

    def __init__(self, tse_path):
        self._transport = Transport(tse_path)

    def start(self):
        response = self._transport.send(TransportCommand.Start)
        return {
            "version": response[0].data.decode(),
            "serial": response[1].data.hex(),
        }

    def get_pin_status(self) -> Tuple[bool, bool, bool, bool]:
        response = self._transport.send(TransportCommand.GetPinStates)
        states = response[0].data
        return list(bool(b) for b in states)

    def initialize_pin_values(self, admin_puk: bytes, admin_pin: bytes, time_admin_puk: bytes, time_admin_pin: bytes):
        self._transport.send(
            TransportCommand.InitializePins,
            [
                (TransportDataType.BYTE_ARRAY, admin_puk),
                (TransportDataType.BYTE_ARRAY, admin_pin),
                (TransportDataType.BYTE_ARRAY, time_admin_puk),
                (TransportDataType.BYTE_ARRAY, time_admin_pin),
            ])

    def factory_reset(self):
        # Magic factory reset procedure pulled from decompiled JAR
        self._transport.send(
            TransportCommand.FactoryReset,
            [(TransportDataType.BYTE_ARRAY, bytes([160, 0, 0, 1, 81, 83, 80, 65]))])
        self._transport.send(
            TransportCommand.FactoryReset,
            [(TransportDataType.BYTE_ARRAY, bytes([0]))])
        self._transport.send(
            TransportCommand.FactoryReset,
            [(TransportDataType.BYTE_ARRAY, bytes([0]))])
