# SPDX-FileCopyrightText: (c) 2021 Artёm IG <github.com/rtmigo>
# SPDX-License-Identifier: MIT

from subprocess import CompletedProcess
from typing import Optional


class ChkpkgException(Exception):
    def __init__(self,
                 message: Optional[str] = None,
                 inner: Optional[BaseException] = None):
        self.message = message
        self.inner = inner


class CompletedProcessError(ChkpkgException):
    def __init__(self,
                 message: Optional[str] = None,
                 inner: Optional[BaseException] = None,
                 process: Optional[CompletedProcess] = None):
        super().__init__(message=message, inner=inner)
        self.process = process

    def __str__(self):
        return "\n".join([
            str(super()),
            f"process: {self.process}",
        ])


class TwineCheckFailed(CompletedProcessError):
    pass


class FailedToInstallPackage(ChkpkgException):
    pass


class CannotInitializeEnvironment(ChkpkgException):
    pass


class CodeExecutionFailed(CompletedProcessError):
    pass
    # def __init__(self,
    #              message="Code execution failed",
    #              inner: Optional[BaseException] = None,
    #              process: Optional[CompletedProcess] = None):
    #     super().__init__(message, inner=inner)
    #
    #     self.message = message
    #     self.process = process
    #
    # def __str__(self):
    #     return "\n".join([
    #         self.message,
    #         f"process: {self.process}",
    #     ])
