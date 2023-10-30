#!/usr/bin/env python3
#
# MIT License
#
# (C) Copyright 2019-2023 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import jwt
import time
import logging

import oauthlib.oauth2
import requests_oauthlib

LOGGER = logging.getLogger(__name__)
TOKEN_HOST = "api-gw-service-nmn.local"  # default in case it is not in the settings configmap

def fetch_token(token_host=TOKEN_HOST):
    # The token will be fetched from Keycloak using the client id and secret
    # from the mounted Kubernetes secret.
    token_url = "https://%s/keycloak/realms/shasta/protocol/openid-connect/token" % token_host
    auth_user_file = "/client_auth/client-id"
    auth_secret_file = "/client_auth/client-secret"
    oauth_client_id = ""
    oauth_client_secret = ""
    f = None
    try:
        f = open(auth_user_file, 'r')
        oauth_client_id = f.readline().rstrip()
    except IOError:
        LOGGER.error("Unable to read user name from %s", auth_user_file)
        return None
    finally:
        if f:
            f.close()
            f = None
    try:
        f = open(auth_secret_file, 'r')
        oauth_client_secret = f.readline().rstrip()
    except IOError:
        LOGGER.error("Unable to read secret from %s", auth_secret_file)
        return None
    finally:
        if f:
            f.close()
            f = None

    oauth_client = oauthlib.oauth2.BackendApplicationClient(
        client_id=oauth_client_id)

    session = requests_oauthlib.OAuth2Session(
        client=oauth_client, auto_refresh_url=token_url,
        auto_refresh_kwargs={
            'client_id': oauth_client_id,
            'client_secret': oauth_client_secret,
        },
        token_updater=lambda t: None)

    # Set the CA Cert file location so that we can use TLS to talk with Keycloak.
    # This certificate is mounted from an existing configmap.
    session.verify = "/ca_public_key/certificate_authority.crt"

    token = session.fetch_token(token_url=token_url, client_id=oauth_client_id,
                                client_secret=oauth_client_secret, timeout=500)

    access_token = None
    if token:
        access_token = token.get("access_token")
        if (access_token is not None):
            LOGGER.debug("Got access_token %s", access_token)
            return access_token
        else:
            LOGGER.error("Unable to get an access_token for client %s",
                         oauth_client_id)
            return None
    else:
        LOGGER.error("Unable to get a token object for client %s",
                     oauth_client_id)
        return None


def token_expiring_soon(bearer_token, min_remaining_valid_time):
    if bearer_token is None:
        return True

    # Just decode the token to extract the value.  The token has already been
    # obtained from Keycloak here and verification gets handled
    # by the API GW when the token is checked.
    tokenMap = None
    try:
        tokenMap = jwt.decode(bearer_token,
                              options={"verify_signature": False})
    except Exception as ex:
        LOGGER.error("Unable to decode JWT.  Error was %s", ex)
        return True

    # Grab the expiration time
    tokenExp = tokenMap.get('exp')
    LOGGER.debug("JWT expiration time=%s" % tokenExp)

    if tokenExp is None:
        LOGGER.error("Unable to extract the expiration 'exp' from the JWT.")
        return True

    # If the current time is at or beyond the token expiration minus an
    # additional buffer time (to allow for a successful boot if used now)
    # then consider this token expiration time too close to expiration
    # and signal that we should request a new token.  The buffer time is
    # configurable but a default is provided if needed.
    tnow = int(time.time())
    tmax = tokenExp - int(min_remaining_valid_time)
    LOGGER.debug("tnow=%s tmax=%s" % (tnow, tmax))
    if tnow >= tmax:
        LOGGER.debug("Detected that JWT will expire soon and needs updating.")
        return True
    else:
        LOGGER.debug("""The current JWT expiration time is acceptable. \
A new JWT will not be requested.""")
        return False
