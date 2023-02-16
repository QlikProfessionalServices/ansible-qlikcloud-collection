#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: reload_task
version_added: "0.1.0"
short_description: Manages reload tasks for apps in Qlik Cloud.
description:
    - Manages reload tasks for apps in Qlik Cloud.
options:
  app_id:
    description:
      - ID of the app to be reloaded
    required: true
  partial:
    description:
      - The task is partial reload or not
    required: false
  time_zone:
    description:
      - The time zone in which the time is specified. (Formatted as an IANA
        Time Zone Database name, e.g. Europe/Zurich.) This field specifies the
        time zone in which the event start/end are expanded. If missing the
        start/end fields must specify a UTC offset in RFC3339 format.
    required: false
  auto_reload:
    description:
      - A flag that indicates whether a reload is triggered when data of the
        app is changed
    required: false
  recurrence:
    description:
      - List of RECUR lines for a recurring event, as specified in RFC5545.
        Note that DTSTART and DTEND lines are not allowed in this field; event
        start and end times are specified in the start and end fields. This
        field is omitted for single events or instances of recurring events
    required: false
  end_date_time:
    description:
      - The time that the task will stop recurring. If the time zone is
        missing, this is a combined date-time value expressing a time with a
        fixed UTC offset (formatted according to RFC3339). If a time zone is
        given, the zone offset must be omitted.
    required: false
  start_date_time:
    description:
      - The time that the task execution start recurring. If the time zone is
        missing, this is a combined date-time value expressing a time with a
        fixed UTC offset (formatted according to RFC3339). If a time zone is
        given, the zone offset must be omitted. Field startDateTime should not
        be before the Unix epoch 00:00:00 UTC on 1 January 1970. Note that the
        empty string value with the empty recurrence array indicates the
        scheduled job is not set.
    required: false
  auto_reload_partial:
    description:
      - A flag that indicates whether it is a partial reload or not for the
        auto reload
    required: false
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
  # Create reload task
  reload_task:
    app_id: 116dbfae-7fb9-4983-8e23-5ccd8c508722
    partial: true
    time_zone: America/Toronto
    auto_reload: true
    recurrence:
      - RRULE:FREQ=DAILY;INTERVAL=1;BYHOUR=11;BYMINUTE=18;BYSECOND=0
      - RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,TU;BYHOUR=13;BYMINUTE=17;BYSECOND=0
    end_date_time: 2022-10-12T23:59:00
    start_date_time: 2022-09-19T11:18:00
    auto_reload_partial: true
'''


from ansible.module_utils.basic import AnsibleModule
from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from qlik_sdk import ReloadTasks


class QlikReloadTaskManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'reload_task'
        self.results = {
            'changed': False,
            'reload_task': {},
        }
        self.resource = {}
        self.client = helper.get_client(module, ReloadTasks)

        super().__init__(module)

    def existing(self):
        '''Return existing reload task'''
        if self.resource != {}:
            return self.resource

        results = self.client.get_reload_tasks(appId=self.module_params["app_id"])
        if len(results) > 0:
            self.resource = results[0]
        return self.resource


def main():
    module_args = dict(
        app_id=dict(type='str', required=True),
        partial=dict(type='bool', required=False),
        time_zone=dict(type='str', required=False),
        auto_reload=dict(type='bool', required=False),
        recurrence=dict(type='list', required=True),
        end_date_time=dict(type='str', required=False),
        start_date_time=dict(type='str', required=False),
        auto_reload_partial=dict(type='bool', required=False),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    spaces = QlikReloadTaskManager(module)
    result = spaces.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
