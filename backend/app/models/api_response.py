""" Response model for API responses. """

from sqlmodel import SQLModel


class APIResponse(SQLModel):
    """
    Represents an API response.

    Attributes:
        status (int): The status code of the response.
        message (str): The message associated with the response.
    """

    status: int
    message: str
