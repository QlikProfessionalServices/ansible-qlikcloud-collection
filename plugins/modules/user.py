#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: user
version_added: "0.1.0"
short_description: Manages users in Qlik Cloud.
description:
    - Manages users in Qlik Cloud.
options:
  subject:
    description:
      - The unique user identitier from an identity provider.
    required: true
  name:
    description:
      - The name of the user.
    required: false
  email:
    description:
      - The email address for the user. This is a required field when inviting a user.
    required: false
  status:
    description:
      - The status of the created user within the tenant.
    required: false
    choices:
      - active
      - invited
      - disabled
      - deleted
  picture:
    description:
      - A static url linking to the avatar of the user.
    required: false
  assigned_roles:
    description:
      - An array of role reference identifiers.
    required: false
    choices:
      - AnalyticsAdmin
      - DataAdmin
      - SharedSpaceCreator
      - ManagedSpaceCreator
      - DataSpaceCreator
      - TenantAdmin
      - Developer
      - AuditAdmin
  allow_recreate:
    description: Allow user to be deleted and recreated if an update is not possible
    default: false
  state:
    description:
      - State of the user
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
  # Create user
  user:
    subject: testuser1
    name: Test User
    email: test.user@qlik.com
    assigned_roles:
      - AnalyticsAdmin
      - Developer
'''


from ansible.module_utils.basic import AnsibleModule

from ansible_collections.qlikprofessionalservices.qlikcloud.plugins.module_utils import helper
from ansible_collections.qlikprofessionalservices.qlikcloud.plugins.module_utils.qlik_manager import QlikCloudManager

from qlik_sdk import Users, Filter


class QlikUserManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'user'
        self.results = {
            'changed': False,
            'user': {},
        }
        self.resource = {}
        self.patchable = [
            'name',
            'assignedRoles',
            'inviteExpiry',
            'preferredZoneInfo',
            'preferredLocale',
            'status']
        self.client = helper.get_client(module, Users)

        super().__init__(module)

    def get_role_ids(self):
        '''Get IDs of the assigned roles'''
        client = helper.get_client(self.module)
        roles = [
            client.roles.get_roles(filter=f'name eq "{role}"')
            for role in self.module_params['assigned_roles']]

        self.desired['assignedRoles'] = [
            {attr: getattr(role[0], attr) for attr in ['id', 'name', 'level', 'type']}
                for role in roles]

    def existing(self):
        '''Return existing space'''
        if self.resource != {}:
            return self.resource

        self.get_role_ids()

        filter = '(status eq "active" or status eq "disabled" or status eq "invited")'
        filter += f' and (subject eq "{self.module_params["subject"]}")'
        query = Filter(filter=filter)
        results = self.client.filter(query)
        if len(results) > 0:
            self.resource = results[0]
        return self.resource

    def update(self):
        if not self.module_params['allow_recreate']:
            self.module.warn('User cannot be updated and allow_recreate set to false')
            return

        self.delete()
        return self.create()


def main():
    module_args = dict(
        subject=dict(type='str', required=True),
        name=dict(type='str', required=False),
        email=dict(type='str', required=False),
        picture=dict(type='str', required=False),
        assigned_roles=dict(type='list', required=False, default=[], options=[
            'AnalyticsAdmin', 'DataAdmin', 'SharedSpaceCreator', 'ManagedSpaceCreator',
            'DataSpaceCreator', 'TenantAdmin', 'Developer', 'AuditAdmin'
        ]),
        status=dict(type='str', required=False),
        state=dict(type='str', required=False, default='present'),
        allow_recreate=dict(type='bool', required=False, default=False),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spaces = QlikUserManager(module)
    result = spaces.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
