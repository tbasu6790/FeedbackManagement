# exceptions.py
class DatabaseConnectionError(Exception):
    pass

class DuplicateFeedbackError(Exception):
    pass

class AuthenticationError(Exception):
    pass

class FileHandlingError(Exception):
    pass
