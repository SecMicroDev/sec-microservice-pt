""" Variables defined by the environment for JWT"""

import os


ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", str(30)))
REFRESH_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("JWT_REFRESH_EXPIRE_MINUTES", str(60 * 24 * 2))
)  # 2 dias
ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_SECRET_DECODE_KEY: str = (
    os.environ["JWT_SECRET_DECODE_KEY"]
    if os.environ.get("ENVIRONMENT", "") == "PROD"
    else os.environ["JWT_SECRET_DECODE_KEY"]
)
JWT_REFRESH_SECRET_KEY = os.environ["JWT_REFRESH_SECRET_KEY"]
