#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: contexts
    version_added: "0.1.0"
    short_description: Uses qlik-cli contexts as an inventory source.
    description:
        - Uses qlik-cli contexts as an inventory source for Qlik Cloud tenants.
    notes:
        - Groups are created for server-type, e.g. cloud, windows.
        - Limited to client-id/secret and api-key authentication.
'''


import yaml

from urllib.parse import urlparse
from pathlib import Path

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):
    NAME = 'contexts'

    def __init__(self):
        super().__init__()
        self._hosts = {}

    def verify_file(self, path):
        ''' return true/false if this is possibly a valid file for this plugin to consume '''
        if super(InventoryModule, self).verify_file(path):
            # base class verifies that file exists and is readable by current user
            if path.endswith(('contexts.yml')):
                return True

            try:
                with open(path, 'r') as stream:
                    yaml_data = yaml.safe_load(stream)
            except Exception as e:
                print(e)
                raise AnsibleParserError(e)

            if ('contexts' in yaml_data
                or ('plugin' in yaml_data and yaml_data['plugin'] == 'qlik.cloud.contexts')):

                return True
            else:
                return False

    def parse(self, inventory, loader, path, cache=False):
        ''' parses the inventory file '''

        # call base method to ensure properties are available for use with other helper methods
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        self.set_options()

        try:
            yaml_data = self.loader.load_from_file(path, cache=False)
        except Exception as e:
            raise AnsibleParserError(e)

        if ((not 'contexts' in yaml_data)
            and ('plugin' in yaml_data and yaml_data['plugin'] == 'qlik.cloud.contexts')):

            path = str(Path.home().joinpath('.qlik/contexts.yml'))
            try:
                yaml_data = self.loader.load_from_file(path, cache=False)
            except Exception as e:
                raise AnsibleParserError(e)

        for context_name, context_data in yaml_data['contexts'].items():
            if not isinstance(context_data, dict):
                context_data = {}

            hostname = urlparse(context_data['server']).hostname
            api_key = context_data.get('headers').get('Authorization')
            if api_key:
                api_key = api_key[7:]
            group = context_data.get('server-type')

            if group:
                self.inventory.add_group(group)
            self.inventory.add_host(context_name, group)
            self.inventory.set_variable(context_name, 'ansible_host', hostname)
            self.inventory.set_variable(context_name, 'ansible_connection', 'local')
            self.inventory.set_variable(context_name, 'client_id', context_data.get('oauth-client-id'))
            self.inventory.set_variable(context_name, 'client_secret', context_data.get('oauth-client-secret'))
            self.inventory.set_variable(context_name, 'access_token', api_key)
