class QDiscoveryError(Exception):
    """Base error that can be safely surfaced to the API."""


class ValidationError(QDiscoveryError):
    code = "INVALID_SCHEMA"


class NoFeasibleBatchError(QDiscoveryError):
    code = "NO_FEASIBLE_BATCH"


class ModelInsufficientDataError(QDiscoveryError):
    code = "MODEL_INSUFFICIENT_DATA"


class QuantumWidthExceededError(QDiscoveryError):
    code = "QUANTUM_WIDTH_EXCEEDED"


class VerificationError(QDiscoveryError):
    code = "VERIFICATION_FAILED"
