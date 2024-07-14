"""
Controls data hashing for the application

The scheme used is bcrypt.  It uses a modified version of the Blowfish stream cipher. 
Featuring a large salt and variable number of rounds, it’s currently the default password 
hash for many systems (notably BSD), and has no known weaknesses. 

Font: (https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html)
"""

from passlib.context import CryptContext


passord_hash = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_data(data: str) -> str:
    """
    Hashes and return str with the configured scheme
    """

    return passord_hash.hash(data)


def validate_hashed_data(data: str, hashed_data: str) -> bool:
    return passord_hash.verify(data, hashed_data)
