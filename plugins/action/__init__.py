#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash
from ansible.module_utils.parsing.convert_bool import boolean


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        # individual modules might disagree but as the generic the action plugin, pass at this point.
        self._supports_check_mode = True
        self._supports_async = True

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        wrap_async = self._task.async_val and not self._connection.has_native_async

        kwargs = {}
        if not 'tenant_uri' in self._task.args:
            kwargs['tenant_uri'] = 'https://' + task_vars.get('ansible_host')
        if not 'api_key' in self._task.args:
            kwargs['api_key'] = task_vars.get('access_token')
        new_module_args = self._task.args | kwargs

        # do work!
        result = merge_hash(result, self._execute_module(module_args=new_module_args, task_vars=task_vars, wrap_async=wrap_async))

        # hack to keep --verbose from showing all the setup module result
        # moved from setup module as now we filter out all _ansible_ from result
        if self._task.action in C._ACTION_SETUP:
            result['_ansible_verbose_override'] = True

        if not wrap_async:
            # remove a temporary path we created
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result