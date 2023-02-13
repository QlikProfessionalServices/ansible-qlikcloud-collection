#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: license_settings
version_added: "0.1.0"
short_description: Manages license settings in Qlik Cloud.
description:
  - Manages license settings in Qlik Cloud.
options:
  auto_assign_analyzer:
    description:
      - If analyzer users are available, they will be automatically assigned. Otherwise, analyzer
        capacity will be assigned, if available.
    required: false
  auto_assign_professional:
    description:
      - If professional users are available, they will be automatically assigned. Otherwise,
        analyzer capacity will be assigned, if available.
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
  license_settings:
    auto_assign_analyzer: yes
    auto_assign_professional: yes

'''


from ansible.module_utils.basic import AnsibleModule

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError

from qlik_sdk import Licenses

class QlikLicenseSettingsManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'license_settings'
        self.results = {
            'changed': False,
            'license_settings': {},
        }
        self.resource = {}
        self.patchable = []
        self.client = helper.get_client(module, Licenses)

        super().__init__(module)

    def existing(self):
        '''Return existing configuration'''
        if self.resource:
            return self.resource
        self.resource = self.client.get_settings()
        return self.resource

    def patch(self):
        self.module.fail_json(
            msg='patch was called but is not valid for license settings',
            **self.results, patch=self.patches)

    def update(self):
        if self.module.check_mode:
            return self.existing()

        try:
            updated = self.client.set_settings(self.desired)
            return updated
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results, patch=self.patches)


def main():
    module_args = dict(
        auto_assign_analyzer=dict(type='bool', required=False),
        auto_assign_professional=dict(type='bool', required=False),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    group_settings = QlikLicenseSettingsManager(module)
    result = group_settings.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
