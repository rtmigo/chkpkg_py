# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT

from subprocess import CompletedProcess
from typing import Optional


class ChkpkgException(Exception):
    def __init__(self, message: str, inner: Optional[BaseException]):
        self.message = message
        self.inner = inner


class TwineCheckFailed(ChkpkgException):
    def __init__(self, inner):
        super().__init__("Twine check failed", inner)


class FailedToInstallPackage(ChkpkgException):
    def __init__(self, inner):
        super().__init__("Failed to install the package", inner)


class CannotInitializeEnvironment(ChkpkgException):
    def __init__(self, inner):
        super().__init__("Cannot initialize environment", inner)


class CodeExecutionFailed(ChkpkgException):
    def __init__(self,
                 message="Code execution failed",
                 inner: Optional[BaseException] = None,
                 process: Optional[CompletedProcess] = None):
        super().__init__(message, inner=inner)

        self.message = message
        self.process = process

    def __str__(self):
        return "\n".join([
            self.message,
            f"process: {self.process}",
        ])
