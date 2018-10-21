#!/usr/bin/env python
#######################################################################
# Copyright (c) 2018 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#######################################################################

"""
Example function to manage (create, delete, list) VMs on AWS.

** REQUIREMENTS **

* secret


Save all required AWS secrets in a JSON file.

cat << EOF > aws.json
{
  "access_key": "<access_key>",
  "secret_key": "<secret_key>",
  "region": "us-west-2"
}
EOF

Create a secret:

dispatch create secret aws aws.json

* image

Create requirements file:

cat << EOF > requirements.txt
boto3==1.9.25
EOF

dispatch create base-image python3-base dispatchframework/python3-base:0.0.13 --language python3
dispatch create image python-aws python3-base --runtime-deps requirements.txt

Create a function:
dispatch create function python-aws aws aws.py --secret aws

Execute it:
dispatch exec aws --wait --input='{"command": "create","name": "exampleVM"}'

"""

import json

import boto3


def list_instances(ec2):
    result = ec2.instances.filter(
        Filters=[
            {
                'Name': 'tag:managedby',
                'Values': ['cloudmaster']
            }
        ]
    )
    return [{
            "id": i.id,
            "name": [t["Value"] for t in i.tags if t["Key"] == "Name"][0],
            "status": i.state["Name"],
            } for i in result if i.state["Name"] != "terminated"]


def create_instance(ec2, name):
    result = ec2.create_instances(
        MinCount=1, MaxCount=1, ImageId="ami-0f47ef92b4218ec09",
        InstanceType="t1.micro",
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'managedby',
                        'Value': 'cloudmaster'
                    },
                    {
                        'Key': 'Name',
                        'Value': name
                    }
                ]
            }
        ])
    instance = result[0]
    return {
        "id": instance.id,
        "name": name,
    }


def delete_instance(ec2_resource, ec2_client, name):
    instances = ec2_resource.instances.filter(
        Filters=[
            {
                'Name': 'tag:managedby',
                'Values': ['cloudmaster']
            },
            {
                'Name': "tag:Name",
                'Values': [name]
            }
        ]
    )
    instanceIds = [i.id for i in instances]
    print(instanceIds)
    return ec2_client.terminate_instances(InstanceIds=instanceIds)


def handle(ctx, payload):
    """
    entry point for AWS commands
    """

    access_key = ctx['secrets']['access_key']
    secret_key = ctx['secrets']['secret_key']
    region = ctx['secrets']['region']

    ec2_resource = boto3.resource("ec2", aws_access_key_id=access_key,
                                  aws_secret_access_key=secret_key, region_name=region)
    ec2_client = boto3.client("ec2", aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key, region_name=region)

    if 'command' not in payload:
        return _error('command is required')
    command = payload['command']

    result = {"error": "command {} is not supported".format(command)}
    if command == 'create':
        result = create_instance(ec2_resource, payload['name'])
    if command == 'list':
        result = list_instances(ec2_resource)
    if command == 'delete':
        result = delete_instance(ec2_resource, ec2_client, payload['name'])

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
