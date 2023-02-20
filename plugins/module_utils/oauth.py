#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native
from ansible.utils.display import Display

from requests.exceptions import HTTPError

from qlik_sdk import AuthType, Config, Auth


def get_access_token(hostname: str, client_id: str, client_secret: str):
    """
    get oauth token for Qlik Cloud tenant

    Parameters
    ----------
    hostname: str
        Hostname of the tenant
    client_id: str
        Client ID for the OAuth client
    client_secret: str
        Client secret associated with the ID
    """
    display = Display()

    client = Auth(Config(
        host=f'https://{hostname}',
        auth_type=AuthType.OAuth2,
        scope=["user_default"],
        client_id=client_id,
        client_secret=client_secret))

    try:
        display.v(f'Requesting access token for client_id of {client_id}')
        token = client.authorize()
        return token
    except HTTPError as err:
        raise AnsibleError('Error getting oauth token, HTTP %s: %s' % (
            err.response.status_code, err.response.text))
    except Exception as err:
        raise AnsibleError('Error getting oauth token: %s' % to_native(err))
