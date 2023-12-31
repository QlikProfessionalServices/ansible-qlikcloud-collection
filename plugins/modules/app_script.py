#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: app_script
version_added: "0.1.0"
short_description: Manages data load script in Qlik Cloud apps.
description:
    - Manages data load script in Qlik Cloud apps.
options:
  app_id:
    description:
      - ID of the app
    required: true
  content:
    description:
      - The content of the script.
  regexp:
    description:
      - Used with C(replace)
        The regular expression to look for in every line of the script.
        Uses Python regular expressions. See U(https://docs.python.org/3/library/re.html).
  replace:
    description:
      - Used with C(regexp)
        The text to replace the matching regexp.
  state:
    description:
      - State of the script
    required: false
    choices:
      - present
      - absent
    default: present
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
  # Set script to load inline table
  qlik.cloud.app_script:
    app_id: 116dbfae-7fb9-4983-8e23-5ccd8c508722
    content: |
      LOAD * INLINE [
        Dim1, Dim2, Value
        A, A01, 100
        B, B01, 40
        B, B02, 60
      ];

  # Set script content from file
  qlik.cloud.app_script:
    app_id: 116dbfae-7fb9-4983-8e23-5ccd8c508722
    content: "{{ lookup('ansible.builtin.file', 'script.qvs') }}"

  # Ensure data connections in script are prefixed with space name
  qlik.cloud.app_script:
    app_id: 116dbfae-7fb9-4983-8e23-5ccd8c508722
    regexp: LIB CONNECT TO '([^:]*)'
    replace: LIB CONNECT TO 'Space Name:\1'
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError
import re

from qlik_sdk import Apps, GenericObjectProperties, GenericObjectEntry


class QlikAppScriptManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'app_script'
        self.results = {
            'changed': False,
            'app_script': {},
        }
        self.resource = {}
        self.states_map = {
            'present': self.ensure_present,
            'absent': self.ensure_absent,
        }
        self.desired = module.params['content']
        self.client: Apps = helper.get_client(module, Apps)

        super().__init__(module)

    @property
    def different(self):
        if self.module_params['regexp']:
            self.desired = re.sub(
                self.module_params['regexp'],
                self.module_params['replace'],
                self.existing(),
                flags=re.I)

        if self.module._diff:
            self.diff['before'] = self.existing()
            self.diff['after'] = self.desired
        return self.desired != self.existing()

    def existing(self):
        '''Return existing app object'''
        if self.resource != {}:
            return self.resource

        try:
            self.resource = self._app.get_script()
        except Exception as err:
            self.module.fail_json(
                msg='Error getting script: %s' % (to_native(err)),
                **self.results)
        return self.resource

    def create(self):
        self.module.fail_json(msg='Script should already exist')

    def update(self):
        if self.module.check_mode:
            self.results['app_object']=helper.asdict(self.resource)
            return self.resource

        self._app.set_script(self.desired)

        return self.desired

    def execute(self):
        '''Execute the desired action according to map of states and actions.'''
        try:
            self._app = self.client.get(self.module_params['app_id'])
        except Exception as err:
            self.module.fail_json(
                msg='Error getting app details: %s; %s' % (to_native(err), self.module_params['api_key']),
                **self.results)

        try:
            session = self._app.open()
        except Exception as err:
            self.module.fail_json(
                msg='Error opening app: %s' % (to_native(err)),
                **self.results)

        with session:
            process_action = self.states_map[self.state]
            process_action()

        if self.module._diff:
            self.results['diff'] = self.diff

        return self.results


def main():
    module_args = dict(
        app_id=dict(type='str', required=True),
        content=dict(type='str'),
        regexp = dict(type='str'),
        replace = dict(type='str'),
        state=dict(
            type='str',
            required=False,
            default='present',
            options=['present', 'absent']),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[('state', 'present', ('content', 'regexp', 'replace'), True)],
        required_together=[('regexp', 'replace')],
        mutually_exclusive=[('content', 'regexp'), ('content', 'replace')],
    )

    manager = QlikAppScriptManager(module)
    result = manager.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
