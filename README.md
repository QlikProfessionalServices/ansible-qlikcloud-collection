# Ansible Collection for Qlik Cloud

This collection (qlik.cloud) includes Ansible modules and plugins to help automate the management of
[Qlik Cloud](https://www.qlik.com/us/products/qlik-cloud) tenants and content.

## Requirements

Tested with Ansible Core >= 2.12.0 versions.

This collection depends on the Qlik SDK for Python (qlik-sdk >= 0.14.0). The Qlik SDK requires
Python >= 3.8.

## Installation

You can install the Qlik Cloud collection with Ansible Galaxy CLI:

```sh
ansible-galaxy collection install qlik.cloud
```

You can also include it in a `requirements.yaml` file and install it with
`ansible-galaxy collection install -r requirements.yaml`, using the format:

```yaml
---
collections:
  - name: qlik.cloud
```

Or clone by your own:

```sh
mkdir -p ~/.ansible/collections/ansible_collections/qlik
git clone https://github.com/qlikprofessionalservices/ansible-qlikcloud-collection.git ~/.ansible/collections/ansible_collections/qlik/cloud
```

The python module dependencies are not installed by ansible-galaxy. They can be manually installed
using pip:

```sh
pip install -r ~/.ansible/collections/ansible_collections/qlik/cloud/requirements.txt
```

Or:

```sh
pip install qlik-sdk
```

## Usage

To use a module from this collection, please reference the full namespace, collection name, and modules name that you want to use:

```yaml
---
- name: Using Qlik Cloud collection
  hosts: mytenant.eu.qlikcloud.com
  tasks:
    - qlik.cloud.space:
        name: myspace
        type: shared
```

Or you can add full namepsace and collection name in the collections element:

```yaml
---
- name: Using Qlik Cloud collection
  hosts: mytenant.eu.qlikcloud.com
  collections:
    - qlik.cloud
  tasks:
    - space:
        name: myspace
        type: shared
```

## License

`qlik.cloud` Ansible collection is [MIT licensed](LICENSE).
