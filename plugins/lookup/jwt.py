#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
  name: jwt
  author: Adam Haydon
  version_added: "0.1.0"
  short_description: Generate a jwt
  description:
      - This lookup generates a jwt for authorisation to a Qlik Cloud tenant.
  options:
    _terms:
      description: The main identifier (aka subject) of the user.
      required: true
    crt:
      description:
        - Private key for signing the token
      type: string
    sub_type:
      description:
        - The type of identifier the sub represents. In this case, user is the
          only applicable value.
      type: string
      default: user
    displayname:
      description:
        - The friendly name to apply to the user.
      required: true
    email:
      description:
        - The email address of the user.
      required: true
    expires_in:
      description:
        - The date/time the JWT expires.
      required: false
    not_before:
      description:
        - The date/time before which the JWT MUST NOT be accepted for
          processing.
      required: false
    issuer:
      description:
        - This is a value created or supplied previously with identity provider
          configuration. It can be a random string.
      required: true
    keyid:
      description:
        - This is a value created or supplied previously with identity provider
          configuration. It can be a random string.
      required: true
    email_verified:
      description:
        - A claim indicating to Qlik that the JWT source has verified that the
          email address belongs to the subject.
      default: true
    jti:
      description:
        - (JWT ID) claim provides a unique identifier for the JWT.
      required: false
    groups:
      description:
        - List of groups to assign to the user.
      required: false
"""


import time

from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from qlik_sdk import generate_signed_token


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        display = Display()

        self.set_options(var_options=variables, direct=kwargs)

        not_before = self.get_option('not_before')
        if not not_before:
            not_before = int(time.time())-5
        expires_in = self.get_option('expires_in')
        if not expires_in:
            expires_in = int(time.time())+300

        ret = []
        for term in terms:
            display.vvvvv(f'Generating jwt for {term}')
            signed_token = generate_signed_token(
                crt=self.get_option('crt'),
                sub=term,
                sub_type=self.get_option('sub_type'),
                name=self.get_option('displayname'),
                email=self.get_option('email'),
                email_verified=self.get_option('email_verified'),
                groups=self.get_option('groups'),
                not_before=not_before,
                expires_in=expires_in,
                keyid=self.get_option('keyid'),
                issuer=self.get_option('issuer'))
            ret.append(signed_token)

        return ret
