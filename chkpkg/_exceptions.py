class TwineCheckFailed(BaseException):
    def __init__(self, e):
        self.inner = e


class FailedToInstallPackage(BaseException):
    def __init__(self, e):
        self.inner = e


class CannotInitializeEnvironment(BaseException):
    def __init__(self, e):
        self.inner = e


class CodeExecutionFailed(BaseException):
    def __init__(self, e):
        self.inner = e