import json
import re
import requests

def i_dont_understand(secrets, payload):
    response = {
        "attachments": [
            {
                "title": "I don't understand",
                "text": "I didn't understand your command... try create [vm name] with [template]",
                "mrkdwn_in": [
                    "text"
                ],
                "color": "danger"
            }
        ]
    }
    resp = requests.post(payload["response_url"], json=response)
    print("response[%s]: %s" % (resp.status_code, resp.text))

def create(secrets, payload):
    '''Handle the create command

    Async call out to the clone-vm function
    '''
    r = re.compile(r"^(?P<command>create)\s(?P<name>.+)\s(from|with)\s(?P<template>.+)\s*$")
    m = r.match(payload["text"])
    if not m:
        return i_dont_understand(secrets, payload)

    params = m.groupdict()

    create_vm = {
        "blocking": False,
        "input": {
            "template": params["template"],
            "name": params["name"],
            "powerOn": True
        },
        "secrets": ["vcenter",]
    }

    print("%s/v1/runs?functionName=%s" % (secrets["url"], "clone-vm"))
    print(create_vm)

    resp = requests.post(
        "%s/v1/runs?functionName=%s" % (secrets["url"], "clone-vm"),
        headers={"Authorization": "Bearer %s" % secrets["jwt"]},
        json=create_vm)

    if resp.status_code == 202:
        response = {
            "response_type": "in_channel",
            "attachments": [
                {
                    "title": "Create VM",
                    "text": "VM creation in progress",
                    "mrkdwn_in": [
                        "text"
                    ],
                    "color": "good"
                }
            ]
        }
    else:
        response = {
            "attachments": [
                {
                    "title": "Create VM",
                    "text": "VM creation failed: [%d] %s" % (resp.status_code, resp.text),
                    "mrkdwn_in": [
                        "text"
                    ],
                    "color": "danger"
                }
            ]
        }
    resp = requests.post(payload["response_url"], json=response)
    print("response[%s]: %s" % (resp.status_code, resp.text))


def echo(secrets, payload):
    '''Pretty silly echo implementation which calls a sub-function to echo.
    '''
    echo = {
        "blocking": True,
        "input": payload
    }
    print("%s/v1/runs?functionName=%s" % (secrets["url"], "echo"))
    print(echo)

    resp = requests.post(
        "%s/v1/runs?functionName=%s" % (secrets["url"], "echo"),
        headers={"Authorization": "Bearer %s" % secrets["jwt"]},
        json=echo)

    if resp.ok and resp.json()["status"] == "READY":
        response = {
            "response_type": "in_channel",
            "attachments": [
                {
                    "title": "Echo",
                    "text": json.dumps(resp.json()["output"]["text"]),
                    "mrkdwn_in": [
                        "text"
                    ],
                    "color": "good"
                }
            ]
        }
    else:
        response = {
            "attachments": [
                {
                    "title": "Echo",
                    "text": "Echo failed: [%d] %s" % (resp.status_code, resp.text),
                    "mrkdwn_in": [
                        "text"
                    ],
                    "color": "danger"
                }
            ]
        }
    resp = requests.post(payload["response_url"], json=response)
    print("response[%s]: %s" % (resp.status_code, resp.text))

def handle(ctx, payload):

    command_name = payload["text"].split()[0]

    commands = {
        "create": create,
        "echo": echo
    }

    command = commands.get(command_name)
    if command is None:
        i_dont_understand(ctx["secrets"], payload)
    else:
        command(ctx["secrets"], payload)
    return {"text": "ok"}