from typing import Tuple

from bdr_tse import transport

class TseConnector:

    def __init__(self, tse_path):
        self._transport = transport.Transport(tse_path)

    def start(self):
        response = self._transport.send(transport.TransportCommand.Start)
        return {
            "version": response[0].data.decode(),
            "serial": response[1].data.hex(),
        }

    def get_pin_status(self) -> Tuple[bool, bool, bool, bool]:
        response = self._transport.send(transport.TransportCommand.GetPinStates)
        states = response[0].data
        return list(bool(b) for b in states)

