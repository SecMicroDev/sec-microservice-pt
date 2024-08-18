import base64
from datetime import datetime, timedelta
from typing import Any, Union

import jwt
from jwt import ExpiredSignatureError
import pytest

from app.auth.jwt_utils import DEFAULT_OPTIONS, decode_jwt_token
import app.auth.settings as st


DEFAULT_DOMAIN_KEYS = ["user", "role", "id"]
DEFAULT_JWT_KEYS = ["exp", "iss", "iat", "sub"]


def get_default_data() -> tuple[dict[str, str], int, dict[str, str]]:
    """
    Get default test_data
    """

    return (
        {
            "JWT_KEY": base64.b64encode("testunsafeinsecurekey".encode("ascii")).decode(
                "ascii"
            ),
            "JWT_ALGO": "HS256",
        },
        30,
        {"user": "fake_user", "role": "Supervisor", "id": "abcdef123456"},
    )


TEST_KEY = """
-----BEGIN PRIVATE KEY-----
MIIJQgIBADANBgkqhkiG9w0BAQEFAASCCSwwggkoAgEAAoICAQCzb7RaAac+vYMz
6dtRIIWOSXkrsAsgT24YiBS7L6Jfc114KB5kXL1h4JbB+/Ulc3zgQvV11OtL/325
ZBnpUjYyp51z72gy5uhbkHDCp1CnXbPI+v1NqGdfZPx4erD7aT6CLqEbOalXWmxv
aYBeIWNJnhbpZj6RLEZQFENnrUWL1C1Mo0yPrXFSplP4ti1IuRsCAg+yT0N5mAfO
DYfrfM9r9iBBt2B+O35e8ne+Mbrjx+v7wFmSKkRD8bFNYK2cOfm2gEx0h8V8d67s
/SB/Ps5yffSs/YpiMfwq7r5ZMmYrBm9e3HQ6kK85uwhWlqh+AQCC5dkAyLyKtnos
sutUa+AbcTZMQsBPG7aHnG3q+G4zGvBcMnlWGqUwDw4JPIOB39anqjXUE0HFE9K9
xCa58XJPl9MlD4QM6xW7+opmcaynXD518HMovavlD0Tgt59z7lnZv6EBSnNUxwG6
Yt9ke2zAr0785KrqTkAAt+/2w+ago1RJazn5z6QqHZBJTdK8XygcLVlZWWXrWpeL
H5ZIPhdqhtivjaK3BMRjp9YKPEDNPRV3LZK4TJ5PQKYPfDbxMosmsogzwBENKbDE
Po7XD8atl7pQAxBaOiF/OTXP29/lhkkeIfLfpdo20m4pO3xh8UV1Gygqg8H+PMMh
Ppn0u3D7Uj3NxNteQvYFJHXmjLjNzwIDAQABAoICAES0WTx7VJPH0YRfnxulla3B
ATXSnrf84d1fwXxYxVXB4QCgb96iydq/uUnGVPvFiAOAb+bxozSCu5twMiGt2lWz
6yxYdy/CTSa+HAbUNKQY0z15qOKCwC39B1SEOd7R0d7bxtEbV3U8iLdyEHY6V395
GjG89ej1KGkCETsR08ax87Rb9HUxBmqMiCt7acRmJ+qxalwuUFou9ZIWiTwIGo2u
fHRdKAO9eOoW8fVvqi0MQBWxdTprl57iXK6RfXgLlMslveCCmgHJ+77/PuGp5Tde
dgCExedKV1EC//w8OXVw7dTHGXPRMV6r+AnbfuFcNdto8ZmEwvhj3UzfJw84jOKg
DImM4Hl0cqkYfNth+3n/pglA3MW6Gm+6VfYawCxRQsS4xOQtO00awJ/xEdDR8rrx
0rlkuK9iStYE9xeR7bGGCPWALNnwxf4EKrEi9al58ANsg6TF/1q+KTuAn4kzQirh
3gXlCXSSld+cApOIKBnd3Aumoa5nTg+VKkz/WEKD6rg/SsgBt58NJLaXumhM13WJ
fupnf3YiHaRo6kFGHuKHPpDARIanslB/nkkIBJNLSYz3IH13zomuaechPSb0XC7C
bv5Mv8Oqm6JAPAgUIjSLKlnA7lxp7WSLP/IOyRtupK6geXldxgWgTnT39V6cTVai
dffCAQwgda4uQd0orPY1AoIBAQDtfNdMA8TQl19oqEIT7AYxdfrRvELmWxDNM6ma
dcC7dv8FhDB35HUGHfHNKDPY3AfG8lRBqwx52QkHtcingEFabty5L4no8RCnD9su
vnlLRN/STjlBVHklUOwd+NgNKJq7x+SGhMQAveF/NvpjhU+xg0mXX6Cm7q3PzirC
FHdkQ4WoM4HMxO+7vbKq3OGcaysHj5IHl7Uoc6VUDvPuP59Hk4AxSa6QPWak6CEb
JQj8p2EZyeivWla4+gWZQlgssrhgPbkTuHYAJ7L8JOoA7PIx2SVVuygLsi+ErTtI
4GHXTic4A6xop7dqtcfE+8RolcE2cvO/gealjJyxFblRlmQtAoIBAQDBbG1Fwn1W
gC0XrosubriAqffHlUbWSb8Q/UZR8N9R334/ypk0cYOXvB/xxfswrE6yT83tf4KT
ydvYPQBUQ06kfBC/4OlLAB9vVglrh7lIcuf0yllj3AspbnoN7CVk6ZcS9zX2dDKd
sLObzRAJxS09EOyKBh0kRs6QY0F8V0c1FPQHtKT1WXcYiS6m5ZrvEQXp0aCSgYQC
hgrxSZJoBIeBH8MKFeg8XweNHqndl7N6g5dlUkZuPTQl3f2isxaqM4a5dz8db0J7
jNfyTdNAIhTLD3flAHnNMrsF6EEkMZpm2y4bX8RWg6RvNKOc3KIwlsC6o6DgI+av
+dlya95tKwtrAoIBAD5rJocjInKUpo3yU1O7IDGVybOgYJD89GCKqJQhSOO8tfB0
Ouz4Dc3qxufeHipsQlsGzCBqXaAU7Curmq5zpjmnk7nUhdHEslTGdRxHEcg3tQAo
cSH7ms+1AioqglaLCog6VJUKhh2PypnOEGdh3X1RfWEc0DOv3d0VWeWizXJ70MBR
sVbpl/znMfN4lI+xFyEomgAG3qVgJ979Ax3meO2uFe5eaFQe30COhk0FIeSN9ZZ6
m/6iptJ9XEVYy6YL3yvkbSWCwPjvdjqRVTOjE1EIuqhaxX61eYnMoh1YZD7bmrE9
Pe5PzoRsfLIIXioC2kJ+WhRGhyGR4IkmpYuNFI0CggEBAIoe8j0BcF1ntEuX8X2b
xRbjyLN1zprRGKZ6Jk/3MJGXheDpvNNtR+n/hdQxa3lLYfsE7+lrx4PffqUAko6Z
bbwZeCB87DsJgGkRyDJIPjAVFbyBDqo3hKT2ZiQxAFb6U05Qx/EQ8uAWQXu9SHmh
mvdjcXXyfbbc9T64EhhHfurR5pzmC3HEjD4yH+VASo3y2wUoE4DrCah/raq1vd2X
dmfnlXBLSoZp2cuVHPnHDXwsId1RjkfEXsu3pRocxs+NceRY2fIb9B6j6cT2fCbs
72o9xoD6AQBd/J1wR6wf28EdPOSBU4PwB2j97uPhzdPiowfkNso3+NCrGvMRQkk0
lrcCggEARp6jTCh6tzvyjsUZmmWMaK6mED6XxR6z7adsVUD6ApnBKvy9gwbxmL3n
S0n67WhwW/5bmllYQciOBWROOE+ktwB4VJFRbWodgMMETBDttcSnSxpdnZJGNcsK
BqXVXw5SKuG+JxdjrSYVBmEZxQGV1eiNqRxHKKnDB5fCFs1tO9FT3kZyQaLlDl+f
GUwrCp0yD0TuUDP5PM7o2De58wt5pUONyBT9qNBuZ5ru0Bz2aU2JMLdEdk4KKRhJ
oNbG3pMI6ngEun1FBCBfXARMZ2oF63RhsH67/wbI7deAohizM+eLtxPskYAsrQus
7HrmRa7ofO8NFWB0IpDH+WQzineHWA==
-----END PRIVATE KEY-----
"""


DEFAULT_OPTIONS = {
    "iss": "openferp.org",
}


JWT_SECRET_ENCODE_KEY = TEST_KEY


DEFAULT_ENCODE_CONFIG = {"JWT_KEY": JWT_SECRET_ENCODE_KEY, "JWT_ALGO": "RS256"}


def create_jwt_token(
    payload: dict,
    expires: int = 3 * 60,
    config: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed token with a defined algorithm and secret
    for signature. The payload is a dict and the expire time is in minutes
    """

    if config is None:
        config = DEFAULT_ENCODE_CONFIG

    current_default_options: dict[str, Union[str, datetime]] = {
        **DEFAULT_OPTIONS,
        "iat": datetime.now(),
    }

    return jwt.encode(
        {
            "exp": (datetime.now() + timedelta(seconds=expires)).timestamp(),
            "sub": str(payload).replace("'", '"'),
            **current_default_options,
        },
        config["JWT_KEY"],
        config["JWT_ALGO"],
    )


def test_correct_jwt_parsing():
    """
    Test correct parsing with defaults
    """

    _, expire_min, val = get_default_data()
    print(*get_default_data())
    valid_time = datetime.now() + timedelta(minutes=expire_min)
    hashed = create_jwt_token(val, expire_min)

    # print(jws.verify(hashed, config['JWT_KEY'], algorithms=config['JWT_ALGO'], verify=True))

    decoded = decode_jwt_token(hashed)

    assert decoded != None

    for k in DEFAULT_OPTIONS:
        assert k in decoded

    assert (decoded["exp"] - valid_time.timestamp()) <= 2

    for k in val.keys():
        assert decoded["sub"][k] == val[k]


def test_expire_raises_exception():
    """
    Test expiration raises exception
    """

    _, _, val = get_default_data()
    hashed = jwt.encode(
        {
            "exp": (datetime.now() - timedelta(minutes=30, milliseconds=1)).timestamp(),
            "sub": str(val).replace("'", '"'),
            **DEFAULT_OPTIONS,
        },
        JWT_SECRET_ENCODE_KEY,
        st.ALGORITHM,
    )

    with pytest.raises(ExpiredSignatureError) as error_context:
        decode_jwt_token(hashed)
        assert error_context is not None
        print(error_context)
