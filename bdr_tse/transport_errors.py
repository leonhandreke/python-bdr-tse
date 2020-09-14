from bdr_tse.exceptions import TransportError


class TransportErrorSECommunicationFailed(TransportError):
    pass


class TransportErrorTSECommandDataInvalid(TransportError):
    pass


class TransportErrorTSEResponseDataInvalid(TransportError):
    pass


class TransportErrorSigningSystemOperationDataFailed(TransportError):
    pass


class TransportErrorRetrieveLogMessageFailed(TransportError):
    pass


class TransportErrorStorageFailure(TransportError):
    pass


class TransportErrorSecureElementDisabled(TransportError):
    pass


class TransportErrorUserNotAuthorized(TransportError):
    pass


class TransportErrorUserNotAuthenticated(TransportError):
    pass


class TransportErrorSeApiNotInitialized(TransportError):
    pass


class TransportErrorUpdateTimeFailed(TransportError):
    pass


class TransportErrorUserIdNotManaged(TransportError):
    pass


class TransportErrorStartTransactionFailed(TransportError):
    pass


class TransportErrorCertificateExpired(TransportError):
    pass


class TransportErrorNoTransaction(TransportError):
    pass


class TransportErrorUpdateTransactionFailed(TransportError):
    pass


class TransportErrorFinishTransactionFailed(TransportError):
    pass


class TransportErrorTimeNotSet(TransportError):
    pass


class TransportErrorNoERS(TransportError):
    pass


class TransportErrorNoKey(TransportError):
    pass


class TransportErrorSeApiNotDeactivated(TransportError):
    pass


class TransportErrorNoDataAvailable(TransportError):
    pass


class TransportErrorTooManyRecords(TransportError):
    pass


class TransportErrorUnexportedStoredData(TransportError):
    pass


class TransportErrorParameterMismatch(TransportError):
    pass


class TransportErrorIdNotFound(TransportError):
    pass


class TransportErrorTransactionNumberNotFound(TransportError):
    pass


class TransportErrorSeApiDeactivated(TransportError):
    pass


class TransportErrorTransport(TransportError):
    pass


class TransportErrorNoStartup(TransportError):
    pass


class TransportErrorNoStorage(TransportError):
    pass
