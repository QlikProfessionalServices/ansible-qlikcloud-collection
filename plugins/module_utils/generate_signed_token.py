#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
import string
import time
import datetime
from typing import List

import jwt


def _generate_id(length: int) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_signed_token(
    crt: str,
    sub: str,
    sub_type: str,
    name: str,
    email: str,
    expires_in: int,
    not_before: int,
    issuer: str,
    keyid: str,
    email_verified: bool = True,
    jti: str = None,
    groups: List[str] = [],
    algorithm: str = "RS256",
    audience: str = "qlik.api/login/jwt-session",
) -> str:
    """
    helper method for generating signed tokens for exchange with the jwt-session auth flow

    Parameters
    ----------
    crt: str
        string containing the private key certificate (ex: PEM formated private key)
    sub: str
        main identifier (aka subject) of the user.
    sub_type: str
        type of identifier the sub represents. In this case, user is the only applicable value.
    name: str
        friendly name to apply to the user.
    email: str
        email address of the user.
    email_verified: bool, default True
        claim indicating that the JWT source has verified that the email address belongs to the subject.
    expires_in: str
        the lifespan of the resulting JWT.
    not_before: str
        time before which the JWT MUST NOT be accepted for processing.
    issuer: str
        value created or supplied previously with identity provider configuration.
    keyid: str
        value created or supplied previously with identity provider configuration.
    jti: str = None
        JWT ID claim provides a unique identifier for the JWT. Needs to be unique
    groups: list[str]
    algorithm: str, default "RS256"
        The algorithm must be set to "RS256"
    audience: str, default "qlik.api/login/jwt-session",
        audience must be set to "qlik.api/login/jwt-session"

    Notes
    -----
    For more information about the JWT-session auth flow,
    please check https://qlik.dev/tutorials/create-signed-tokens-for-jwt-authorization

    Example
    --------
    >>> with open('private_key.pem') as f:
    ...   private_key = f.read()
    ...   signed_token = generate_signed_token(
    ...       crt=private_key,
    ...       sub="test-user-id",
    ...       sub_type="user",
    ...       name="Hardcore Harry",
    ...       email="harry@example.com",
    ...       email_verified=True,
    ...       groups=["Administrators", "HardCoreGroup"],
    ...       expires_in=datetime.datetime.now() + datetime.timedelta(minutes=30),
    ...       not_before=0,
    ...       keyid="platform-sdks-jwt",
    ...       issuer="https://platform-sdks.qlik.dev",
    ...   )
    """
    if jti is None:
        jti = _generate_id(8)
    current_time = int(datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y%m%d%H%M%S"))
    claims = {
        "jti": jti,
        "sub": sub,
        "subType": sub_type,
        "name": name,
        "email": email,
        "email_verified": email_verified,
        "groups": groups,
        "exp": int(time.time())+300,
        "nbf": int(time.time())-5,
        "iat": int(time.time()),
        "iss": issuer,
        "aud": audience,
    }
    singning_options = {"kid": keyid}
    token = jwt.encode(
        payload=claims, key=crt, algorithm=algorithm, headers=singning_options
    )
    return token
