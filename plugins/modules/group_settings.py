#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: group_settings
version_added: "0.1.0"
short_description: Manages group settings in Qlik Cloud.
description:
  - Manages group settings in Qlik Cloud.
options:
  auto_create_groups:
    description:
      - Determines if groups should be created on login.
    required: true
  sync_idp_groups:
    description:
      - Determines if groups should be created on login.
    required: true
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
  group_settings:
    auto_create_groups: yes
    sync_idp_groups: yes

'''


from ansible.module_utils.basic import AnsibleModule

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError

from qlik_sdk import Groups


class QlikGroupSettingsManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'group_settings'
        self.results = {
            'changed': False,
            'group_settings': {},
        }
        self.resource = {}
        self.patchable = ['autoCreateGroups', 'syncIdpGroups']
        self.client = helper.get_client(module, Groups)

        super().__init__(module)

    def existing(self):
        '''Return existing configuration'''
        if self.resource:
            return self.resource
        self.resource = self.client.get_settings()
        return self.resource

    def patch(self):
        if self.module.check_mode:
            return self.existing()

        try:
            self.client.patch_settings(self.patches)
            return self.client.get_settings()
        except HTTPError as err:
            self.module.fail_json(
                msg='Error patching %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results, patch=self.patches)

    def update(self):
        self.module.fail_json(
            msg='update was called but is not valid for group settings',
            **self.results, patch=self.patches)


def main():
    module_args = dict(
        auto_create_groups=dict(type='bool', required=True),
        sync_idp_groups=dict(type='bool', required=True),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    group_settings = QlikGroupSettingsManager(module)
    result = group_settings.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
