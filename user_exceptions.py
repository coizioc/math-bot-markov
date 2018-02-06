class Error(Exception):
    """Base class for exceptions."""
    pass

class InputError(Error):
    """Exception raised for bad input."""

    def __init__(self, name, output):
        self.name = name
        self.output = output

class AmbiguousInputError(InputError):
    """Exception raised for input that can be interpreted in multiple ways."""
    pass

class NoUserInputError(InputError):
    """Exception raised for input that refers to no user."""
    pass
