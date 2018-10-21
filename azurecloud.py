#!/usr/bin/env python
#######################################################################
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#######################################################################

"""
Example function to manage (create, delete, list) VMs in Azure.

** REQUIREMENTS **

* secret

you can  obtain clientId, password and tenant when creating a service principal. you can create service principal
in Azure by using Azure CLI:

az ad sp create-for-rbac --name principalName --password "" # empty password will generate a random one

Save all required secrets in a JSON file.

cat << EOF > azure.json
{
    "clientId": "<UUID>",
    "password": "<UUID>",
    "tenant": "<UUID>",
    "subscription": "<UUID>",
    "admin_password": "<Password for admin account within a VM>",
    "location": "<Azure region, e.g. eastus2>",
    "subnet": "<name of the subnet to connect VM to>",
    "virtual_network": "<name of the virtual network where the subnet resides>"
}
EOF

Create a secret:

dispatch create secret azure azure.json

* image

Create requirements file:

cat << EOF > requirements.txt
azure==4.0.0
EOF

dispatch create base-image python3-base dispatchframework/python3-base:0.0.13 --language python3
dispatch create image python-azure python3-base --runtime-deps requirements.txt

Create a function:
dispatch create function python-azure azure azurecloud.py --secret azure

Execute it:
dispatch exec azure --wait --input='{"command": "create","name": "exampleVM"}'

"""

import json
import traceback

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

from msrestazure.azure_exceptions import CloudError


def get_credentials(client_id, secret, tenant):
    """Creates Azure credentials object from string credentials"""

    credentials = ServicePrincipalCredentials(
        client_id=client_id,
        secret=secret,
        tenant=tenant
    )
    return credentials


def list_instances(compute_client):
    """Returns a list of instances managed by cloudmaster"""

    return [{
            "id": vm.id,
            "name": vm.name,
            "status": vm.provisioning_state,
            "tags": vm.tags
            } for vm in compute_client.virtual_machines.list_all()
            if vm.tags and 'managedby' in vm.tags and vm.tags['managedby'] == 'cloudmaster']


def create_nic(network_client, location, resource_group, virtual_network, subnet, vm_name):
    """Creates a network interface required by a VM"""

    subnet = network_client.subnets.get(resource_group, virtual_network, subnet)
    async_nic_creation = network_client.network_interfaces.create_or_update(
        resource_group,
        "{}-nic".format(vm_name),
        {
            'location': location,
            'ip_configurations': [{
                'name': 'random_name',
                'subnet': {
                    'id': subnet.id
                }
            }]
        }
    )
    return async_nic_creation.result(timeout=1)


def delete_nic(network_client, resource_group, name):
    """Delete network interface"""
    network_client.network_interfaces.delete(resource_group, "{}-nic".format(name))


def create_instance(compute_client, location, resource_group, nic, name, admin_password):
    """Creates an Azure VM. expects Network interface to be pre-created."""
    try:
        vm_parameters = {
            'location': location,
            'hardware_profile': {
                'vm_size': 'Standard_DS1_v2'
            },
            'tags': {
                'managedby': 'cloudmaster'
            },
            'os_profile': {
                'computer_name': name,
                'admin_username': 'dispatch',
                'admin_password': admin_password
            },
            'storage_profile': {
                'image_reference': {
                    'publisher': 'Canonical',
                    'offer': 'UbuntuServer',
                    'sku': '16.04.0-LTS',
                    'version': 'latest'
                },
            },
            'network_profile': {
                'network_interfaces': [{
                    'id': nic.id,
                }]
            },
        }
        async_vm_creation = compute_client.virtual_machines.create_or_update(
            resource_group, name, vm_parameters)
        vm = async_vm_creation.result(timeout=1)
        return {
            "id": vm.id,
            "name": vm.name,
            "state": vm.provisioning_state,
            "tags": vm.tags
        }
    except CloudError:
        return _error(traceback.format_exc())


def delete_instance(compute_client, resource_group, name):
    """Delete an instance"""
    try:
        async_vm_deletion = compute_client.virtual_machines.delete(resource_group, name)
        return async_vm_deletion.result(timeout=1)
    except CloudError:
        return _error(traceback.format_exc())


def _error(error_msg):
    return json.dumps({
        'error': error_msg
    })


def handle(ctx, payload):
    """entrypoint for Azure operations """
    resource_group = ctx['secrets']['resource_group']
    location = ctx['secrets']['location']
    subscription = ctx['secrets']['subscription']
    admin_password = ctx['secrets']['admin_password']
    subnet = ctx['secrets']['subnet']
    virtual_network = ctx['secrets']['virtual_network']

    credentials = get_credentials(client_id=ctx['secrets']['clientId'],
                                  secret=ctx['secrets']['password'],
                                  tenant=ctx['secrets']['tenant'])

    compute_client = ComputeManagementClient(credentials, subscription)
    network_client = NetworkManagementClient(credentials, subscription)

    if 'command' not in payload:
        return _error('command is required')
    command = payload['command']

    # default result is unsupported command
    result = {"error": "command {} is not supported".format(command)}

    if command == 'create':

        if 'name' not in payload:
            return _error('vm name is required')
        vm_name = payload['name']

        nic = create_nic(network_client, location,resource_group, virtual_network, subnet, vm_name)
        result = create_instance(compute_client, location, resource_group, nic, vm_name, admin_password)

    if command == 'list':
        result = list_instances(compute_client)

    if command == 'delete':
        result = delete_instance(compute_client, resource_group, payload['name'])
        delete_nic(network_client, resource_group, payload['name'])

    return result


if __name__ == "__main__":
    import sys

    with open(sys.argv[1]) as p:
        payload = json.load(p)

    with open(sys.argv[2]) as s:
        secrets = json.load(s)
    ctx = {
        "secrets": secrets
    }
    print("payload: ", payload, file=sys.stderr)
    print("secrets: ", secrets, file=sys.stderr)
    retval = handle(ctx, payload)
    print(retval, file=sys.stdout)
