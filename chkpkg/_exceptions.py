# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT

class ChkpkgException(BaseException):
    def __init__(self, e):
        self.inner = e


class TwineCheckFailed(ChkpkgException):
    def __init__(self, e):
        super().__init__(e)


class FailedToInstallPackage(ChkpkgException):
    def __init__(self, e):
        super().__init__(e)


class CannotInitializeEnvironment(ChkpkgException):
    def __init__(self, e):
        super().__init__(e)


class CodeExecutionFailed(ChkpkgException):
    def __init__(self, e):
        super().__init__(e)
