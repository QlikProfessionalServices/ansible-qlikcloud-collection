#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: web_integration
version_added: "0.1.0"
short_description: Manages web integrations in Qlik Cloud.
description:
  - Manages web integrations in Qlik Cloud.
options:
  name:
    description:
      - Name of the web integration.
    required: false
  valid_origins:
    description:
      - List of origins that are valid for the web integration.
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
  # Create web integration
  web_integration:
    name: Website
    valid_origins: https://www.qlik.com

'''


from ansible.module_utils.basic import AnsibleModule

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from qlik_sdk import WebIntegrations


class QlikWebIntegrationManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'web_integration'
        self.results = {
            'changed': False,
            'web_integration': {},
        }
        self.resource = {}
        self.patchable = ['validOrigins']
        self.client = helper.get_client(module, WebIntegrations)

        super().__init__(module)

    def existing(self):
        '''Return existing configuration'''
        if self.resource:
            return self.resource

        webints = self.client.get_web_integrations()
        for integration in webints:
            if integration.name == self.module_params['name']:
                self.resource = integration
                return integration

        return self.resource


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        valid_origins=dict(type='list', required=False),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    group_settings = QlikWebIntegrationManager(module)
    result = group_settings.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
