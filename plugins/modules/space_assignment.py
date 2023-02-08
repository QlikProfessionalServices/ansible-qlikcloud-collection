#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: space_assignment
version_added: "0.1.0"
short_description: Manages space assignments in Qlik Cloud.
description:
    - Manages space assignments in Qlik Cloud.
options:
  space:
    description: The space to assign access
    required: true
  type:
    description:
      - Type of assignment
    required: true
    choices:
      - group
      - user
  roles:
    description: The roles assigned to the assigneeId
    required: true
    choices:
      - consumer
      - contributor
      - dataconsumer
      - facilitator
      - operator
      - producer
      - publisher
      - basicconsumer
  assignee_id:
    description: The userId or groupId based on the type
    required: true
  state:
    description:
      - State of the space
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
  # Create assignment
  space_assignment:
    space: Test
    type: group
    assignee_id: 639b0f044791a8f1f20aed23
    roles:
      - consumer
'''


from ansible.module_utils.basic import AnsibleModule

from ansible_collections.qlikprofessionalservices.qlikcloud.plugins.module_utils import helper
from ansible_collections.qlikprofessionalservices.qlikcloud.plugins.module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError

from qlik_sdk import Spaces


class QlikAssignmentManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'assignment'
        self.results = {
            'changed': False,
            'assignment': {},
        }
        self.resource = {}
        self._space = None
        self.client = helper.get_client(module, Spaces)

        super().__init__(module)

    @property
    def space(self):
        if self._space:
            return self._space

        space_results = self.client.get_spaces(name=self.module_params['space'])
        if len(space_results) == 0:
            self.module.fail_json(msg="Space not found!", **self.results)
        for space in space_results:
            if space.name == self.module_params['space']:
                self._space = space
                return self._space

    def existing(self):
        '''Return existing space'''
        if self.resource != {}:
            return self.resource

        space_assignments = self.space.get_assignments(limit=100)
        for assignment in space_assignments:
            if assignment.type != self.desired['type']:
                continue
            if assignment.assigneeId != self.desired['assigneeId']:
                continue
            self.resource = assignment
            return assignment

        return {}

    def create(self):
        if self.module.check_mode:
            return self.existing()

        try:
            return self.space.create_assignment(dict(
              assigneeId=self.desired['assigneeId'],
              roles=self.desired['roles'],
              type=self.desired['type'],
              spaceId=self.space.id,
            ))
        except HTTPError as err:
            self.module.fail_json(
                msg='Error creating assignment, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results, desired=self.desired)

    def delete(self):
        if self.module.check_mode:
            return {}

        try:
            self.client.delete_assignment(self.existing().id, self.space.id)
            return {}
        except HTTPError as err:
            self.module.fail_json(
                msg='Error deleting assignment, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results)

    def update(self):
        if self.module.check_mode:
            return self.existing()

        try:
            return self.client.set_assignment(self.existing().id, self.space.id, self.desired)
        except HTTPError as err:
            self.module.fail_json(
                msg='Error updating assignment, HTTP %s: %s' % (
                    err.response.status_code, err.response.text),
                **self.results, desired=self.desired)


def main():
    module_args = dict(
        space=dict(type='str', required=True),
        type=dict(type='str', required=True),
        assignee_id=dict(type='str', required=True),
        roles=dict(type='list', required=True, options=[
            'consumer', 'contributor', 'dataconsumer', 'facilitator',
            'operator', 'producer', 'publisher', 'basicconsumer'
        ]),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    assignment = QlikAssignmentManager(module)
    result = assignment.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
