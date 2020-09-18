import os
import re
import os.path
import time
import mmap
import logging

import construct

from bdr_tse.exceptions import TimeoutException

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
BLOCK_SIZE = 8192

# The token that we always send to the TSE in the header
TOKEN = bytes([0xDE, 0xAD, 0xBE, 0xEF])

HEADER_CON = "header" / construct.Const(
    bytes(
        [
            0x41,
            0x64,
            0x56,
            0x61,
            0x6E,
            0x63,
            0x45,
            0x44,
            0x20,
            0x53,
            0x65,
            0x43,
            0x75,
            0x52,
            0x65,
            0x20,
            0x53,
            0x44,
            0x2F,
            0x4D,
            0x4D,
            0x43,
            0x20,
            0x43,
            0x41,
            0x72,
            0x64,
            0x01,
        ]
    )
)

TOKEN_CON = "token" / construct.Const(TOKEN)
RANDOM_TOKEN_CON = "random_token" / construct.Byte[4]

MSC_TRANSPORT_DISABLE_SUSPEND_PACKET = construct.Padded(
    BLOCK_SIZE,
    construct.Struct(
        HEADER_CON,
        TOKEN_CON,
        construct.Const(bytes([0x00, 0x02, 0x53, 0x44, 0x00, 0x00])),
    ),
)

MSC_TRANSPORT_ENABLE_SUSPEND_PACKET = construct.Padded(
    BLOCK_SIZE,
    construct.Struct(
        HEADER_CON,
        TOKEN_CON,
        construct.Const(bytes([0x00, 0x02, 0x53, 0x45, 0x00, 0x00])),
    ),
)

MSC_TRANSPORT_SUSPEND_RESPONSE_PACKET = construct.Padded(
    BLOCK_SIZE,
    construct.Struct(HEADER_CON, RANDOM_TOKEN_CON, construct.Const(bytes([0x00]))),
)

MSC_TRANSPORT_COMMAND_PACKET = construct.Padded(
    BLOCK_SIZE,
    construct.Struct(
        HEADER_CON,
        TOKEN_CON,
        "command_data_length"
        / construct.Rebuild(
            construct.Int16ub, construct.len_(construct.this.command_data)
        ),
        construct.Const(bytes([0x00, 0x00])),
        "command_data" / construct.Byte[construct.this.command_data_length],
    ),
)

MSC_TRANSPORT_RESPONSE_PACKET = construct.Padded(
    BLOCK_SIZE,
    construct.Struct(
        HEADER_CON,
        RANDOM_TOKEN_CON,
        "response_data" / construct.Prefixed(construct.Int16ub, construct.GreedyBytes),
    ),
)


def _format_hex_for_log(data: bytes, length=200) -> str:
    return " ".join(re.findall("....", data.hex()[:length]))


class MscTransport:
    """Transport adapter that implements the mass storage class (MSC) interface to
    the TSE. This transport adapter uses a single file in the root directory of the
    user-accessible portion of the TSE, named ``TSE-IO.bin``, for communication.
    By writing to and reading from this file (bypassing OS buffers) request/response
    cycles can be exchanged with the TSE."""

    CMD_FILENAME = "TSE-IO.bin"

    def __init__(self, tse_path):
        self.tse_path = tse_path

        # Get an aligned chunk of memory, required for O_DIRECT
        # See http://www.alexonlinux.com/direct-io-in-python
        self._aligned_buf = mmap.mmap(-1, BLOCK_SIZE)
        # O_DIRECT is required to bypass OS buffers. Keeping the file open between
        # read and write seems to be required.
        self._fd = os.open(self._get_tse_cmd_filepath(), os.O_RDWR | os.O_DIRECT)
        self.set_suspend(False)

    def close(self):
        """Suspend and close the connection to the TSE."""
        self.set_suspend(True)
        os.close(self._fd)
        self._aligned_buf.close()

    def _get_tse_cmd_filepath(self):
        return os.path.join(self.tse_path, MscTransport.CMD_FILENAME)

    def set_suspend(self, suspend: bool, timeout=DEFAULT_TIMEOUT):
        """Sets the suspend mode of the TSE."""
        packet = (
            MSC_TRANSPORT_ENABLE_SUSPEND_PACKET
            if suspend
            else MSC_TRANSPORT_DISABLE_SUSPEND_PACKET
        )
        self._write_block(packet.build({}))

        # Ensure that the operation was completed successfully by parsing the response.
        data = self._read_until_ready(timeout=timeout)
        MSC_TRANSPORT_SUSPEND_RESPONSE_PACKET.parse(data)

    def write(self, command_data: bytes):
        """Write a block of command data to the TSE.

        :param command_data: The command data to write
        """
        data = MSC_TRANSPORT_COMMAND_PACKET.build({"command_data": command_data})
        self._write_block(data)

    def read(self, timeout=DEFAULT_TIMEOUT):
        """Read a response to a command from the TSE. Will wait until a reply is
         ready.

        :param timeout: The timeout for waiting for a reply.
        :return: The response data.
        """
        data = self._read_until_ready(timeout=timeout)
        packet = MSC_TRANSPORT_RESPONSE_PACKET.parse(data)
        # TODO(Leon Handreke): Implement multi-fragment response

        if packet.random_token == TOKEN:
            # TODO(Leon Handreke): Better exception
            raise Exception

        return packet.response_data

    def _write_block(self, data: bytes):
        self._aligned_buf.seek(0)
        self._aligned_buf.write(data)

        os.lseek(self._fd, 0, os.SEEK_SET)
        logger.debug("Write: " + _format_hex_for_log(data))
        os.writev(self._fd, [self._aligned_buf])

    def _read_block(self) -> bytes:
        self._aligned_buf.seek(0)

        os.lseek(self._fd, 0, os.SEEK_SET)
        os.readv(self._fd, [self._aligned_buf])

        self._aligned_buf.seek(0)
        data = self._aligned_buf.read(BLOCK_SIZE)
        logger.debug("Read: " + _format_hex_for_log(data))

        return data

    def _read_until_ready(self, timeout) -> bytes:
        max_time = time.time() + timeout
        # TODO(Leon Handreke): Timeout
        while time.time() < max_time:
            data = self._read_block()
            if data[32:34] != bytes([0xFF, 0xFF]):
                return data
            time.sleep(0.05)

        raise TimeoutException
