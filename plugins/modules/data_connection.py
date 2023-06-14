#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: data_connection
version_added: "0.1.0"
short_description: Manages data connection in Qlik Cloud.
description:
    - Manages data connections in Qlik Cloud.
options:
  data_source_id:
    description:
      - ID of the datasource, list of datasources can be obtained from 'GET /v1/datasources'
    required: true
  connection_name:
    description:
      - Name of the data connection
    required: true
    aliases:
      - name
  space:
    description:
      - Name of the space where the data connection exists
    required: false
  connection_properties:
    description:
      - List of connection properties required to create dataconnection for a given datasource,
        which is defined by the response of 'GET /v1/dataconnections/apispec'
    required: true
  state:
    description:
      - State of the data connection
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
  # Create Databricks connection
  data_connection:
    datasource_id: databricks
    connection_name: DatabricksAPI-StandardRequest
    space: DCaaS
    connection_properties:
      host: test.azuredatabricks.net
      port: 443
      catalog: default
      schema: default
      http_path: /
      auth_mech: 3
      username: username
      password: secret
      ssl: true

  # Create REST connection
  data_connection:
    datasource_id: rest
    connection_name: RestAPI-StandardRequest
    space: DCaaS
    connection_properties:
      url: https://tenant.qlikcloud.com/api/v1/items

  # Create Amazon S3 V2 connection
  qlikprofessionalservices.qlikcloud.data_connection:
    data_source_id: AmazonS3ConnectorV2
    connection_name: AmazonS3V2API-StandardRequest
    space: DCaaS
    connection_properties:
      accessKey: "1234"
      secretKey: "1234"
      region: eu-west-1
      bucketName: mybucket

  # Create Salesforce connection
  qlikprofessionalservices.qlikcloud.data_connection:
    data_source_id: sfdc
    connection_name: SfdcAPI-StandardRequest
    space: DCaaS
    connection_properties:
      sfEnvironment: custom
      envDomain: sandbox-dev-ed.develop.my.salesforce.com
      authenticator: salesforce
      UserId: sandbox@qlik
      SFpassword: secret
      sftoken: "1234"

  # Create Google BigQuery connection
  qlikprofessionalservices.qlikcloud.data_connection:
    data_source_id: gbq
    connection_name: GBQAPI-ServiceAuthRequest
    space: DCaaS
    connection_properties:
      OAuthMechanism: 0
      email: user@domain.com
      catalog: default
      key_file_path:
        - name: gbq_key
          value: "{{ lookup('file', 'gbq_key') | b64encode }}"
      p12_custom_pwd: secret

  # Create Google Cloud Storage connection
  qlikprofessionalservices.qlikcloud.data_connection:
    data_source_id: File_GoogleCloudStorageConnector
    connection_name: GCSAPI-StandardRequest
    space: DCaaS
    connection_properties:
      serviceAccountKeyFile:
        - name: gbq_key
          value: "{{ lookup('file', 'gbq_key') | b64encode }}"
      bucketName: mybucket

  # Create SFTP connection
  qlikprofessionalservices.qlikcloud.data_connection:
    data_source_id: File_FileTransferConnector
    connection_name: SftpAPI-StandardRequest-PrivateKeyFile
    space: DCaaS
    connection_properties:
      host: sftp.domain.com
      sftpPort: 22
      publicKeyAlgorithm: RSA
      publicKey: "{{ lookup('file', lookup('env','HOME') + '/.ssh/id_rsa.pub') | b64encode }}"
      username: alice
      privateKey:
        - name: id_rsa
          value: "{{ lookup('file', lookup('env','HOME') + '/.ssh/id_rsa') | b64encode }}"
'''


from ansible.module_utils.basic import AnsibleModule
from ..module_utils import helper
from ..module_utils.qlik_manager import QlikCloudManager

from requests.exceptions import HTTPError

from qlik_sdk import ListableResource


class QlikDataConnectionManager(QlikCloudManager):
    def __init__(self, module: AnsibleModule):
        self.type = 'data_connection'
        self.results = {
            'changed': False,
            'data_connection': {},
        }
        self.resource = {}
        self._space_id = ''
        self.client = helper.get_client(module)

        super().__init__(module)

    @property
    def different(self):
        return False

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

        query_params = {'spaceId': self.space_id} if self.space_id else {'personal': True}

        response = self.client.rest(path='/data-connections', params=query_params)
        results = ListableResource(
            response=response.json(),
            auth=self.client.auth,
            path="/data-connections",
        )
        for conn in results.pagination:
            if conn['qName'] == self.module_params['connection_name']:
                self.resource = conn
                break

        return self.resource

    def create(self):
        if self.module.check_mode:
            self.results['data_connection']=helper.asdict(self.resource)
            return self.results

        self.desired['spaceId'] = self.space_id
        self.results.update({'desired': self.desired})
        try:
            response = self.client.rest(
                path="/dcaas/data-connections",
                method="POST",
                params={},
                data=helper.asdict(self.desired),
                timeout=60,
            )
        except HTTPError as err:
            self.module.fail_json(
                msg='Error creating %s, HTTP %s: %s' % (
                    self.type, err.response.status_code, err.response.text),
                **self.results)
        result = response.json()
        return result

    def update(self):
        return self.resource


def main():
    module_args = dict(
        data_source_id=dict(type='str', required=True),
        connection_name=dict(type='str', required=True, aliases=['name']),
        space=dict(type='str', required=False),
        connection_properties=dict(type='dict', required=True),
        state=dict(type='str', required=False, default='present'),
        tenant_uri=dict(type='str', required=True),
        api_key=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    manager = QlikDataConnectionManager(module)
    result = manager.execute()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
