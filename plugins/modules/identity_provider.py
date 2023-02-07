#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: identity_provider
version_added: "0.1.0"
short_description: Manages identity providers in Qlik Cloud.
description:
  - Manages identity providers in Qlik Cloud.
options:
  description:
    description:
      - Description of the identity provider
    required: true
  tenant_ids:
    description:
      - The tenant identifiers that map to the given IdP
    required: false
  protocol:
    description:
      - The protocol to be used for communicating with the identity provider
    required: true
    choices:
      - OIDC
      - jwtAuth
  provider:
    description:
      - The identity provider to be used
    required: true
    choices:
      - external
      - auth0
      - okta
      - generic
      - salesforce
      - keycloak
      - adfs
      - azureAD
  clock_tolerance_sec:
    description:
      - There can be clock skew between the IdP and Qlik's login server, in these cases a tolerance
      - can be set, decimals will be rounded off
    required: false
  options:
    description: Required IdP configurations
    required: false
  tenant_uri:
    description:
      - Base URI of the tenant
    required: true
  api_key:
    description:
      - Bearer token for authentication
    required: true
'''

EXAMPLES = '''
  # Create JWT IdP
  identity_provider:
    description: JWT
    protocol: jwtAuth
    provider: external
    options:
      jwtLoginEnabled: true
      issuer: https://auth.mydomain.com
      staticKeys:
        - kid: my_key_identifier
          pem: "{{ lookup('file', 'publickey.pem') }}"

'''


from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils import helper
from ansible.module_utils.qlik_manager import QlikCloudManager

from qlik_sdk import IdentityProviders


class QlikIdentityProviderManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'identity_provider'
        self.results = {
            'changed': False,
            'identity_provider': {},
        }
        self.resource = {}
        self.patchable = ['active', 'description', 'meta', 'options', 'clockToleranceSec']
        self.client = helper.get_client(module, IdentityProviders)

        super().__init__(module)

    def existing(self, field_name="description"):
        '''Return existing configuration'''
        if self.resource:
            return self.resource

        all_idps = self.client.get_identity_providers(limit=100)
        for provider in all_idps:
            if provider.description == self.module_params[field_name]:
                self.resource = provider
                return provider

        return self.resource

    def update(self):
        self.delete()
        return self.create()


def main():
    module_args = dict(
        description=dict(type='str', required=True),
        tenant_ids=dict(type='list', required=False),
        protocol=dict(type='str', required=True),
        provider=dict(type='str', required=True),
        clock_tolerance_sec=dict(type='int', required=False),
        options=dict(type='dict', required=False),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    identity_provider = QlikIdentityProviderManager(module)
    result = identity_provider.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
