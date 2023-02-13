#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: generate_jwt
version_added: "0.1.0"
short_description: Generate JWT tokens for use with Qlik Cloud.
description:
    - Generate JWT tokens for use with Qlik Cloud.
options:
  crt:
    description:
      - Private key for signing the token.
    required: true
  sub:
    description:
      - Subject the JWT is issued to.
    required: true
  sub_type:
    description:
      - Type of entity the token is issued to.
    required: false
    choices:
      - user
    default: user
  name:
    description:
      - Name of the user.
    required: true
  email:
    description:
      - Email address of the user.
    required: true
  expires_in:
    description:
      - Number of seconds until the token expires.
    required: false
  not_before:
    description:
      - Not before time of the token.
    required: false
  issuer:
    description:
      - Token issuer.
    required: true
  keyid:
    description:
      - ID of the key.
    required: true
  email_verified:
    description:
      - Specifies if the email address of the user has been verified.
    required: True
    default: true
  jti:
    description:
      - Token ID.
    required: false
  groups:
    description:
      - List of groups to assign to the user.
    required: false
'''

EXAMPLES = '''
  # Generate a JWT
  generate_jwt:
    crt: "{{ lookup('file', 'privatekey.pem') }}"
    sub: test-user
    name: Test User
    email: test.user@qlik.com
    groups:
      - Tester
    keyid: "my_issuer_key"
    issuer: https://my-idp.qlik.com
'''


import time

from ansible.module_utils.basic import AnsibleModule

# from ansible_collections.qlikprofessionalservices.qlikcloud.plugins.module_utils.generate_signed_token import generate_signed_token
from qlik_sdk import generate_signed_token

def main():
    module_args = dict(
        crt=dict(type='str', required=True),
        sub=dict(type='str', required=True),
        sub_type=dict(type='str', default='user'),
        name=dict(type='str', required=True),
        email=dict(type='str', required=True),
        expires_in=dict(type='int', required=False),
        not_before=dict(type='int', required=False),
        issuer=dict(type='str', required=True),
        keyid=dict(type='str', required=True),
        email_verified=dict(type='bool', default=True),
        jti=dict(type='str', required=False),
        groups=dict(type='list', required=False, default=[])
    )

    result = dict(
        changed=False,
        original_message='',
        message='',
        jwt=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    signed_token = generate_signed_token(
      crt=module.params['crt'],
      sub=module.params['sub'],
      sub_type=module.params['sub_type'],
      name=module.params['name'],
      email=module.params['email'],
      email_verified=module.params['email_verified'],
      groups=module.params['groups'],
      not_before=int(time.time())-5,
      expires_in=int(time.time())+300,
      keyid=module.params['keyid'],
      issuer=module.params['issuer'])
    result['jwt'] = signed_token

    module.exit_json(**result)


if __name__ == '__main__':
    main()
