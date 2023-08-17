#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: content_security_policy
version_added: "0.1.0"
short_description: Manages content security policy origins in Qlik Cloud.
description:
  - Manages content security policy origins in Qlik Cloud.
options:
  name:
    description:
      - Name of the content security policy.
    required: true
  origin:
    description:
      - Origins that the policy applies to.
    required: true
  imgSrc:
    description:
      - Indicates the policy applies to images and favicons.
    required: false
  fontSrc:
    description:
      - Indicates the policy applies to fonts.
    required: false
  childSrc:
    description:
      - Indicates the policy applies to frames and web workers.
    required: false
  frameSrc:
    description:
      - Indicates the policy applies to frames.
    required: false
  mediaSrc:
    description:
      - Indicates the policy applies to audio and video.
    required: false
  styleSrc:
    description:
      - Indicates the policy applies to style sheets.
    required: false
  objectSrc:
    description:
      - Indicates the policy applies to object, embed, and applets.
    required: false
  scriptSrc:
    description:
      - Indicates the policy applies to scripts.
    required: false
  workerSrc:
    description:
      - Indicates the policy applies to web workers.
    required: false
  connectSrc:
    description:
      - Indicates the policy applies to URLs loaded in scripts.
    required: false
  formAction:
    description:
      - Indicates the policy applies to form submissions.
    required: false
  connectSrcWSS:
    description:
      - Indicates the policy applies to websockets.
    required: false
  frameAncestors:
    description:
      - Indicates the policy applies to parent web contexts that embed the page.
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
  # Create content security policy
  qlik.cloud.content_security_policy:
    name: Website
    origin: https://www.qlik.com

'''


from ansible.module_utils.basic import AnsibleModule

from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError

from qlik_sdk import CspOrigins


class QlikCspOriginManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'csp_origin'
        self.results = {
            'changed': False,
            'csp_origin': {},
        }
        self.resource = {}
        self.patchable = ['validOrigins']
        self.client = helper.get_client(module, CspOrigins)

        super().__init__(module)

    def existing(self):
        '''Return existing configuration'''
        if self.resource:
            return self.resource

        csp = self.client.get_csp_origins(name=self.module_params['name'])
        if len(csp) > 0:
            self.resource = csp[0]

        return self.resource


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        origin=dict(type='str', required=False),
        imgSrc=dict(type='bool', required=False),
        fontSrc=dict(type='bool', required=False),
        childSrc=dict(type='bool', required=False),
        frameSrc=dict(type='bool', required=False),
        mediaSrc=dict(type='bool', required=False),
        styleSrc=dict(type='bool', required=False),
        objectSrc=dict(type='bool', required=False),
        scriptSrc=dict(type='bool', required=False),
        workerSrc=dict(type='bool', required=False),
        connectSrc=dict(type='bool', required=False),
        formAction=dict(type='bool', required=False),
        connectSrcWSS=dict(type='bool', required=False),
        frameAncestors=dict(type='bool', required=False),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True, no_log=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    group_settings = QlikCspOriginManager(module)
    result = group_settings.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
