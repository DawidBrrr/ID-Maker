

class ImageProcessingException(Exception):
    """Wyjątek dla błędów przetwarzania obrazów"""
    pass

class ValidationException(Exception):
    """Wyjątek dla błędów walidacji"""
    pass

class RateLimitException(Exception):
    """Wyjątek dla przekroczenia limitów"""
    pass

class TaskNotFoundException(Exception):
    """Wyjątek gdy task nie został znaleziony"""
    pass