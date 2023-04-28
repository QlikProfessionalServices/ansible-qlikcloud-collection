#!/usr/bin/python
# -*- coding: utf-8 -*-

class QlikDiff:
    def __init__(self, existing: dict, desired: dict):
        self.existing = existing
        self.desired = desired
        self.differences = []
        self.diff = {'before': {}, 'after': {}}

    @property
    def patch(self):
        result = []
        for attr in self.differences:
            result.append({'op': 'replace', 'path': f'/{attr}', 'value': self.desired[attr]})
        return result

    def is_different(self):
        '''Returns true if existing space is different to module params, otherwise false'''
        different = False
        for attr in self.desired:
            if self.desired[attr] is None:
                continue
            if self.desired[attr] != self.existing.get(attr):
                different = True
                self.differences.append(attr)

        self._update_diff()
        return different

    def _update_diff(self):
        for attr in self.differences:
            self.diff['before'].update({attr: self.existing.get(attr)})
            self.diff['after'].update({attr: self.desired[attr]})

    def can_patch(self, patchable_attributes: list):
        for attr in self.diff['after']:
            if attr not in patchable_attributes:
                return False
        return True

    def get_changes(self):
        changes = {}
        for attr in self.differences:
            changes[attr] = self.desired[attr]
        return changes

    def apply_changes(self):
        for attr in self.differences:
            self.existing[attr] = self.desired[attr]
        return self.existing