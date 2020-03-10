class SdkFatalError(Exception):
    """An error that cannot be recovered from"""

class SdkPemError(SdkFatalError):
    """Local PEM file is not usable"""

class SdkServerConnectionError(SdkFatalError):
    """Socket connection to server failed"""

class SdkServerRequestError(SdkFatalError):
    """HTTP request to server failed"""

class SdkServerSslError(Exception):
    """Cannot verify server connection due to an SSL error. Triggers PEM refresh."""

class SdkApiResponseError(SdkFatalError):
    """API response indicates unsuccessful operation"""
    def __init__(self, message, httpStatus = 0):
        super(SdkApiResponseError, self).__init__(message)
        self.httpStatus = httpStatus
