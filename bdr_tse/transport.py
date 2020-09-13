from typing import Tuple, List, Union
import enum
import time

import construct

from bdr_tse import msc_transport


# 0x8000:
# return ErrorSECommunicationFailed;
# 0x8001:
# return ErrorTSECommandDataInvalid;
# 0x8002:
# return ErrorTSEResponseDataInvalid;
# 0x8003:
# return ErrorSigningSystemOperationDataFailed;
# 0x8004:
# return ErrorRetrieveLogMessageFailed;
# 0x8005:
# return ErrorStorageFailure;
# 0x8006:
# return ErrorSecureElementDisabled;
# 0x8007:
# return ErrorUserNotAuthorized;
# 0x8008:
# return ErrorUserNotAuthenticated;
# 0x8009:
# return ErrorSeApiNotInitialized;
# 0x800A:
# return ErrorUpdateTimeFailed;
# 0x800B:
# return ErrorUserIdNotManaged;
# 0x800C:
# return ErrorStartTransactionFailed;
# 0x800D:
# return ErrorCertificateExpired;
# 0x800E:
# return ErrorNoTransaction;
# 0x800F:
# return ErrorUpdateTransactionFailed;
# 0x8010:
# return ErrorFinishTransactionFailed;
# 0x8011:
# return ErrorTimeNotSet;
# 0x8012:
# return ErrorNoERS;
# 0x8013:
# return ErrorNoKey;
# 0x8014:
# return ErrorSeApiNotDeactivated;
# 0x8015:
# return ErrorNoDataAvailable;
# 0x8016:
# return ErrorTooManyRecords;
# 0x8017:
# return ErrorUnexportedStoredData;
# 0x8018:
# return ErrorParameterMismatch;
# 0x8019:
# return ErrorIdNotFound;
# 0x801A:
# return ErrorTransactionNumberNotFound;
# 0x801B:
# return ErrorSeApiDeactivated;
# 0x801C:
# return ErrorTransport;
# 0x801D:
# return ErrorNoStartup;
# 0x801E:
# return ErrorNoStorage;

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


class TransportDataType(enum.IntEnum):
    BYTE = 0x01
    BYTE_ARRAY = 0x02
    SHORT = 0x03
    STRING = 0x04
    UINT32ARRAY = 0x05


TransportDataTupleType = Tuple[TransportDataType, Union[bytes, int, str, List[int]]]

TRANSPORT_DATA_PARAMETER = construct.Struct(
    "data_type" / construct.Int8ub,
    "data" / construct.Prefixed(construct.Int16ub, construct.GreedyBytes))

TRANSPORT_COMMAND_PACKET = construct.Struct(
    construct.Const(bytes([0x5C, 0x54])),
    "command" / construct.Int16ub,
    "command_data" / construct.Prefixed(
        construct.Int16ub,
        construct.GreedyRange(TRANSPORT_DATA_PARAMETER))
)

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
            "command_data": list({"data_type": p[0], "data": p[1]} for p in params),
        })

    def _decode(self, data):
        return TRANSPORT_RESPONSE_PACKET.parse(data)

    def send(self, cmd, params: List[TransportDataTupleType] = []):
        self._transport.write(self._encode(cmd, params))
        return self._decode(self._transport.read()).response_data
