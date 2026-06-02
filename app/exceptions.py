class AppError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidURLError(AppError):
    def __init__(self, message: str = "Invalid or unsupported URL"):
        super().__init__(message, 400)


class VideoNotAvailableError(AppError):
    def __init__(self, message: str = "Video not available"):
        super().__init__(message, 404)


class AgeRestrictedError(AppError):
    def __init__(self, message: str = "Video is age-restricted"):
        super().__init__(message, 403)


class ExtractionError(AppError):
    def __init__(self, message: str = "Could not process this video"):
        super().__init__(message, 502)
