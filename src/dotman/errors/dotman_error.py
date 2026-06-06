class DotmanError(Exception):
    """Base class for all dotman errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.__class__.__name__

    def print_error(self):
        print(self.message)
