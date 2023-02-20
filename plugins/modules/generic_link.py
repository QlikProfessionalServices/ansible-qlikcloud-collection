#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: generic_link
version_added: "0.1.0"
short_description: Manages links in Qlik Cloud.
description:
    - Manages links in Qlik Cloud.
options:
  name:
    description:
      - Name of the link
    required: true
  description:
    description:
      - Description of the link
    required: true
  link:
    description:
      - URL of the link
    required: true
  owner_id:
    description:
      - ID of the owner
    required: true
  space_id:
  state:
    description:
      - State of the link
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
  # Create link
  generic_link:
    name: Qlik website
    link: https://www.qlik.com
'''


from ansible.module_utils.basic import AnsibleModule

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from qlik_sdk import ListableResource

class QlikLinkManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'link'
        self.results = {
            'changed': False,
            'link': {},
        }
        self.resource = {}
        self._space_id = ''

        super().__init__(module)

    @property
    def space_id(self):
        if self._space_id:
            return self._space_id
        if self.module_params['space'] == '':
            return ''

        space_results = self.client.spaces.get_spaces(name=self.module_params['space'])
        if len(space_results) == 0:
            self.module.fail_json(msg="Space not found!", **self.results)
        for space in space_results:
            if space.name == self.module_params['space']:
                self._space_id = space.id
                return self._space_id

    def existing(self):
        '''Return existing reload task'''
        if self.resource != {}:
            return self.resource

        query_params = {'name': self.module_params['name']}
        if self.space_id is not None:
            query_params['spaceId'] = self.space_id
        response = self.client.rest(
            path="/generic-links",
            method="GET",
            params=query_params,
            data=None,
        )
        results = ListableResource(
            response=response.json(),
            auth=self.client.auth,
            path="/generic-links",
        )
        if len(results) > 0:
            self.resource = results[0]

        return self.resource

    def create(self):
        if self.module.check_mode:
            self.results['link']=helper.asdict(self.resource)
            return self.results

        self.desired['spaceId'] = self.space_id
        response = self.client.rest(
            path="/generic-links",
            method="POST",
            params={},
            data=helper.asdict(self.desired),
        )
        result = response.json()
        return result

    def delete(self):
        if self.module.check_mode:
            self.results['link']=helper.asdict(self.resource)
            return self.results

        self.client.rest(
            path=f"/generic-links/{self.resource['id']}",
            method="DELETE",
            params={},
            data=helper.asdict(self.desired),
        )

    def update(self):
        if self.module.check_mode:
            self.results['link']=helper.asdict(self.resource)
            return self.results

        self.desired['spaceId'] = self.space_id
        response = self.client.rest(
            path=f"/generic-links/{self.resource['id']}",
            method="PUT",
            params={},
            data=helper.asdict(self.desired),
        )
        result = response.json()
        return result


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        description=dict(type='str', required=False),
        link=dict(type='str', required=True),
        owner_id=dict(type='str', required=False),
        space=dict(type='str', required=False),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spaces = QlikLinkManager(module)
    result = spaces.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()