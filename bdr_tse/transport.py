from typing import Tuple, List, Union
import enum
import time

import construct

from bdr_tse import msc_transport
from bdr_tse import exceptions
from bdr_tse.transport_errors import *

TRANSPORT_ERROR_CODES = {
    0x8000: TransportErrorSECommunicationFailed,
    0x8001: TransportErrorTSECommandDataInvalid,
    0x8002: TransportErrorTSEResponseDataInvalid,
    0x8003: TransportErrorSigningSystemOperationDataFailed,
    0x8004: TransportErrorRetrieveLogMessageFailed,
    0x8005: TransportErrorStorageFailure,
    0x8006: TransportErrorSecureElementDisabled,
    0x8007: TransportErrorUserNotAuthorized,
    0x8008: TransportErrorUserNotAuthenticated,
    0x8009: TransportErrorSeApiNotInitialized,
    0x800A: TransportErrorUpdateTimeFailed,
    0x800B: TransportErrorUserIdNotManaged,
    0x800C: TransportErrorStartTransactionFailed,
    0x800D: TransportErrorCertificateExpired,
    0x800E: TransportErrorNoTransaction,
    0x800F: TransportErrorUpdateTransactionFailed,
    0x8010: TransportErrorFinishTransactionFailed,
    0x8011: TransportErrorTimeNotSet,
    0x8012: TransportErrorNoERS,
    0x8013: TransportErrorNoKey,
    0x8014: TransportErrorSeApiNotDeactivated,
    0x8015: TransportErrorNoDataAvailable,
    0x8016: TransportErrorTooManyRecords,
    0x8017: TransportErrorUnexportedStoredData,
    0x8018: TransportErrorParameterMismatch,
    0x8019: TransportErrorIdNotFound,
    0x801A: TransportErrorTransactionNumberNotFound,
    0x801B: TransportErrorSeApiDeactivated,
    0x801C: TransportErrorTransport,
    0x801D: TransportErrorNoStartup,
    0x801E: TransportErrorNoStorage,
}

class TransportCommand(enum.IntEnum):
    Start = 0x0000,

    GetPinStates = 0x0001
    InitializePins = 0x0002

    AuthenticateUser = 0x0003
    UnblockUser = 0x0004
    Logout = 0x0005

    Initialize = 0x0006
    UpdateTime = 0x0007
    GetSerialNumbers = 0x0008
    MapERStoKey = 0x0009

    StartTransaction = 0x000A
    UpdateTransaction = 0x000B
    FinishTransaction = 0x000C

    ExportData = 0x000D
    GetCertificates = 0x000E
    ReadLogMessage = 0x000F
    Erase = 0x0010

    GetConfigData = 0x0011
    GetStatus = 0x0012

    Deactivate = 0x0013
    Activate = 0x0014
    Disable = 0x0015

    # new in SE - API version 2.0
    ExportMoreData = 0x0016
    GetERSMappings = 0x0017
    GetKeyData = 0x0018
    GetWearIndicator = 0x0019

    # new in SE - API version 2.1
    DeleteUpTo = 0x001B
    Shutdown = 0x00FF

    # Not documented, pulled from decompiled Factory Reset JAR
    FactoryReset = 42
    FirmwareUpdate = 99
    UpdateCertificate = 26


class TransportDataType:
    BYTE = 0x01
    BYTE_ARRAY = 0x02
    SHORT = 0x03
    STRING = 0x04
    LONG_ARRAY = 0x05


TransportDataTupleType = Tuple[TransportDataType, Union[bytes, int, str, List[int]]]

TRANSPORT_DATA_PARAMETER = construct.Select(
        # BYTE
        construct.Struct(
            "data_type" / construct.Const(bytes([TransportDataType.BYTE])),
            construct.Const(bytes([0x00, 0x01])),
            "data" / construct.Byte),
        # BYTE_ARRAY
        construct.Struct(
            "data_type" / construct.Const(bytes([TransportDataType.BYTE_ARRAY])),
            "data" / construct.Prefixed(construct.Int16ub, construct.GreedyBytes)),
        # SHORT
        construct.Struct(
            "data_type" / construct.Const(bytes([TransportDataType.SHORT])),
            construct.Const(bytes([0x00, 0x02])),
            "data" / construct.Int16ub),
        # STRING
        construct.Struct(
            "data_type" / construct.Const(bytes([TransportDataType.STRING])),
            "data" / construct.Prefixed(construct.Int16ub, construct.GreedyString("ascii"))),
        # LONG_ARRAY
        construct.Struct(
            "data_type" / construct.Const(bytes([TransportDataType.LONG_ARRAY])),
            construct.Const(bytes([0x00, 0x02])),
            "data" / construct.Prefixed(construct.Int16ub, construct.GreedyRange(construct.Int32ub)))
)

TRANSPORT_COMMAND_PACKET = construct.Struct(
    construct.Const(bytes([0x5C, 0x54])),
    "command" / construct.Int16ub,
    "command_data" / construct.Prefixed(
        construct.Int16ub,
        construct.GreedyRange(TRANSPORT_DATA_PARAMETER))
)

TRANSPORT_COMMAND_RAW_PACKET = construct.Struct(
    construct.Const(bytes([0x5C, 0x54])),
    "command" / construct.Int16ub,
    "command_data" / construct.Prefixed(
        construct.Int16ub, construct.GreedyBytes)
)

TRANSPORT_ERROR_RESPONSE_PACKET = construct.Struct(
    "error_code" / construct.Int16ub)

TRANSPORT_RESPONSE_PACKET = construct.Struct(
    "response_data" / construct.Prefixed(
        construct.Int16ub,
        construct.GreedyRange(TRANSPORT_DATA_PARAMETER))
)


class Transport:
    def __init__(self, tse_path):
        self._transport = msc_transport.MscTransport(tse_path)

    def _encode(self, cmd, params: List[TransportDataTupleType]) -> bytes:
        return TRANSPORT_COMMAND_PACKET.build({
            "command": cmd,
            "command_data": list({"data_type": bytes([p[0]]), "data": p[1]} for p in params),
        })

    def _decode(self, data):
        return TRANSPORT_RESPONSE_PACKET.parse(data)

    def send(self, cmd, params: List[TransportDataTupleType] = []):
        self._transport.write(self._encode(cmd, params))
        raw_response = self._transport.read()

        # If MSB is set, response is an error
        if raw_response[0] & 0x80:
            error_response = TRANSPORT_ERROR_RESPONSE_PACKET.parse(raw_response)
            raise TRANSPORT_ERROR_CODES.get(error_response.error_code, exceptions.BdrTseException)

        response = TRANSPORT_RESPONSE_PACKET.parse(raw_response)
        return response.response_data
