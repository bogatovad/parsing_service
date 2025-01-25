class RunUsecaseException(Exception):
    """Exception raised for errors in the RunUsecase.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Error in RunUsecase") -> None:
        self.message = message
        super().__init__(self.message)
