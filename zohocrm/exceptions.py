class BaseError(Exception):
    pass


class UnknownError(BaseError):
    pass


class InvalidModuleError(BaseError):
    pass


class NoPermissionError(BaseError):
    pass


class MandatoryKeyNotFoundError(BaseError):
    pass


class InvalidDataError(BaseError):
    pass


class InvalidDataRIndexError(BaseError):
    pass


class MandatoryFieldNotFoundError(BaseError):
    pass


class InvalidDataTypeError(BaseError):
    pass
