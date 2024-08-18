from sqlmodel import SQLModel


class TokenData(SQLModel):
    username: str
    password: str
    # scopes: List[str] = []
    # token_type: str = "bearer"
