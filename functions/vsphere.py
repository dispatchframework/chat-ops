#!/usr/bin/env python
#######################################################################
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#######################################################################

"""
Example function to manage (create, delete, list) VMs in vSphere.

** REQUIREMENTS **

* secret

Store all the required secrets in a JSON file.

cat << EOF > vsphere.json
{
  "host": "vCenter URL",
  "datacenter": "SDDC-Datacenter",
  "resourcePool": "Compute-ResourcePool",
  "vmFolder": "Workloads",
  "username": "<username>",
  "password": "<password>"
}
EOF

Create a secret:

dispatch create secret vsphere vsphere.json

* image

Create requirements file:

cat << EOF > requirements.txt
pyvmomi==6.7.0.2018.9
EOF

dispatch create base-image python3-base dispatchframework/python3-base:0.0.3 --language python3
dispatch create image python-vsphere python3-base --runtime-deps requirements.txt

Create a function:
dispatch create function python-vsphere vsphere vsphere.py --secret vsphere

Execute it:
dispatch exec vsphere --wait --input='{"command": "create","name": "exampleVM"}'

"""

import json
import ssl

from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect


def get_obj(content, vimtype, name):
    """Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break
    return obj


def list_vms(vm_folder):
    """Returns a list of instances managed by cloudmaster"""

    return [
        {
            'name': vm.summary.config.name,
            'id': vm.summary.config.instanceUuid,
            'status': vm.runtime.powerState,
        }
        for vm in vm_folder.childEntity]


def create_vm(content, template, vm_name, datacenter_name, vm_folder, resource_pool, power_on):
    """
    Clone a VM from a template/VM, datacenter_name, vm_folder, datastore_name
    cluster_name, resource_pool, and power_on are all optional.
    """

    # if none get the first one
    datacenter = get_obj(content, [vim.Datacenter], datacenter_name)

    if vm_folder:
        destfolder = get_obj(content, [vim.Folder], vm_folder)
    else:
        destfolder = datacenter.vmFolder

    resource_pool = get_obj(content, [vim.ResourcePool], resource_pool)

    relospec = vim.vm.RelocateSpec()
    relospec.datastore = template.datastore[0]
    relospec.pool = resource_pool

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = power_on

    print("creating VM...")
    print("clone spec: %s" % clonespec)
    task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    return clonespec, task.info.state


def delete_vm(content, name):
    """Delete an instance"""
    vm = get_obj(content, [vim.VirtualMachine], name)
    if vm:
        vm.Destroy_Task()
    return {
        'status': 'vm deletion started'
    }


def _error(error_msg):
    return json.dumps({
        'error': error_msg
    })


def handle(ctx, payload):
    """entrypoint for vSphere operations"""

    template_name = 'dispatch-photon'

    secrets = ctx["secrets"]
    if secrets is None:
        raise Exception("Requires vsphere secrets")

    host = secrets.get("host")
    port = secrets.get("port", 443)
    dc_name = secrets.get("datacenter")
    vm_folder = secrets.get("vmFolder")
    resource_pool = secrets.get("resourcePool")
    username = secrets.get("username")
    password = secrets.get("password", "")

    vm_name = payload.get("name")
    power_on = payload.get("powerOn", False)

    if 'command' not in payload:
        return _error('command is required')
    command = payload['command']

    # default result is unsupported command
    result = {"error": "command {} is not supported".format(command)}

    context = None
    if hasattr(ssl, '_create_unverified_context'):
        context = ssl._create_unverified_context()
    si = SmartConnect(
        host=host,
        user=username,
        pwd=password,
        port=port,
        sslContext=context)

    content = si.RetrieveContent()

    if command == 'create':
        template = get_obj(content, [vim.VirtualMachine], template_name)
        if template is None:
            _error("template not found")
            return
        _, result = create_vm(content, template, vm_name, dc_name, vm_folder, resource_pool, power_on)

    if command == 'list':
        folder = get_obj(content, [vim.Folder], vm_folder)
        result = list_vms(folder)

    if command == 'delete':
        result = delete_vm(content, vm_name)

    Disconnect(si)

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
