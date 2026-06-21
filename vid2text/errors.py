class Vid2TextError(Exception):
    exit_code = 2


class UserError(Vid2TextError):
    exit_code = 1


class NetworkError(Vid2TextError):
    exit_code = 2


class TranscodeError(Vid2TextError):
    exit_code = 2


class ModelError(Vid2TextError):
    exit_code = 2
