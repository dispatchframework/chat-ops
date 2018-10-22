#!/usr/bin/env python
#######################################################################
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#######################################################################

"""
Example function to manage (create, delete, list) VMs on GCP.

** REQUIREMENTS **

* secret

Save all required GCP secrets in a JSON file. the file should contain the service account secrets downloaded as JSON file,
plus additional entry for a zone.

cat << EOF > gcp.json
{
  "type": "service_account",
  "project_id": "<project_id>",
  ... Other service account credentials
  "zone": "us-west1-c"
}

EOF

Create a secret:

dispatch create secret gcp gcp.json

* image

Create requirements file:

cat << EOF > requirements.txt
google-api-python-client==1.7.4
EOF

dispatch create base-image python3-base dispatchframework/python3-base:0.0.13 --language python3
dispatch create image python-gcp python3-base --runtime-deps requirements.txt

Create a function:
dispatch create function python-gcp gcp gcp.py --secret gcp

Execute it:
dispatch exec gcp --wait --input='{"command": "create","name": "exampleVM"}'

"""

import time
import json

import googleapiclient.discovery
from google.oauth2 import service_account


def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone, filter="labels.managedby=cloudmaster").execute()
    if 'items' in result:
        return result['items']
    else:
        return []


def create_instance(compute, project, zone, name):
    image_response = compute.images().getFromFamily(
        project='debian-cloud', family='debian-9').execute()
    source_disk_image = image_response['selfLink']

    machine_type = "zones/%s/machineTypes/n1-standard-1" % zone

    config = {
        'name': name,
        'machineType': machine_type,
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
            ]
        }],
        'labels': {
            'managedby': 'cloudmaster',
        }
    }

    return compute.instances().insert(
        project=project,
        zone=zone,
        body=config).execute()


def delete_instance(compute, project, zone, name):
    return compute.instances().delete(
        project=project,
        zone=zone,
        instance=name).execute()


# may not be needed
def wait_for_operation(compute, project, zone, operation):
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(result['error'])
            return result

        time.sleep(1)


def gcp_creds(secret):
    return service_account.Credentials.from_service_account_info(json.loads(secret))


def handle(ctx, payload):
    """
    entry point for GCP commands
    """

    creds = gcp_creds(json.dumps(ctx['secrets']))
    zone = ctx['secrets']['zone']
    project = ctx['secrets']['project_id']

    compute = googleapiclient.discovery.build('compute', 'v1', credentials=creds, cache_discovery=False)

    if 'command' not in payload:
        return _error('command is required')
    command = payload['command']

    result = {"error": "command {} is not supported".format(command)}
    if command == 'create':
        result = create_instance(compute, project, zone, payload['name'])
    if command == 'list':
        result = list_instances(compute, project, zone)
    if command == 'delete':
        result = delete_instance(compute, project, zone, payload['name'])

    return result


def _error(error_msg):
    return json.dumps({
            'error': error_msg
        })


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
