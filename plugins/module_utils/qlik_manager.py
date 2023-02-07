#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils import helper
from ansible.module_utils.qlik_diff import QlikDiff

from requests.exceptions import HTTPError


class QlikCloudManager:
    def __init__(self, module: AnsibleModule):
        self.module = module
        self.module_params = module.params
        self.diff = {}
        self.patches = []
        self.patched = {}
        self.changes = {}

        self.state = self.module_params['state'] if 'state' in self.module_params else 'present'
        if not hasattr(self, 'resource'):
            self.resource = {}
        if not hasattr(self, 'desired'):
            self.desired = helper.construct_state_from_params(module.params)
        if not hasattr(self, 'client'):
            self.client = helper.get_client(module)
        if not hasattr(self, 'results'):
            self.results = {
                'changed': False,
            }
        if not hasattr(self, 'patchable'):
            self.patchable = []

    @property
    def exists(self):
        return bool(self.existing() != {})

    def existing(self):
        return self.resource

    @property
    def different(self):
        '''Returns true if existing resource is different to module params, otherwise false'''
        diffcheck = QlikDiff(existing=helper.asdict(self.existing()), desired=self.desired)
        is_different = diffcheck.is_different()
        if is_different:
            if diffcheck.can_patch(self.patchable):
                self.patches = diffcheck.patch
                self.patched = diffcheck.apply_changes()
            else:
                self.changes = diffcheck.get_changes()
        diffs = diffcheck.diff
        if self.module._diff and is_different and diffs['before'] and diffs['after']:
            self.diff['before'] = "\n".join(
                ["%s - %s" % (k, v) for k, v in sorted(
                    diffs['before'].items())]) + "\n"
            self.diff['after'] = "\n".join(
                ["%s - %s" % (k, v) for k, v in sorted(
                    diffs['after'].items())]) + "\n"
        return is_different

    def create(self):
        if self.module.check_mode:
            return self.existing()

        try:
            new_resource = self.client.create(self.desired)
            return new_resource
        except HTTPError as err:
            self.module.fail_json(
                msg='Error creating %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results)

    def delete(self):
        if self.module.check_mode:
            return {}

        try:
            self.resource.delete()
            return {}
        except HTTPError as err:
            self.module.fail_json(
                msg='Error deleting %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results)

    def patch(self):
        if self.module.check_mode:
            return self.existing()

        try:
            self.resource.patch(self.patches)
            return self.patched
        except HTTPError as err:
            self.module.fail_json(
                msg='Error patching %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results, patch=self.patches)

    def update(self):
        if self.module.check_mode:
            return self.existing()

        try:
            updated = self.resource.update(self.desired)
            return updated
        except HTTPError as err:
            self.module.fail_json(
                msg='Error patching %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results, patch=self.patches)

    def ensure_present(self):
        '''Ensure the resource exists'''
        if not self.exists:
            self.results[self.type] = helper.asdict(self.create())
            self.results['changed'] = True
            return

        if not self.different:
            self.results[self.type] = helper.asdict(self.existing())
            return

        if self.patches:
            self.results[self.type] = helper.asdict(self.patch())
            self.results['changed'] = True
            return

        self.results[self.type] = helper.asdict(self.update())
        self.results['changed'] = True

    def ensure_absent(self):
        '''Ensure the resource does not exist'''
        if self.exists:
            self.delete()
            self.results['changed'] = True

    def execute(self):
        '''Execute the desired action according to map of states and actions.'''
        states_map = {
            'present': self.ensure_present,
            'absent': self.ensure_absent
        }
        process_action = states_map[self.state]
        process_action()

        if self.module._diff:
            self.results['diff'] = self.diff

        return self.results
