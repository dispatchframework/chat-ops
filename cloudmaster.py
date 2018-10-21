import json
import re
import requests

CLOUDS = ['aws', 'azure', 'gcp', 'vsphere']


def i_dont_understand(payload):
    """Prints help message when user provides unsupported command"""

    response = {
        "attachments": [
            {
                "title": "I don't understand",
                "text": "I didn't understand your command... try:\n"
                        "• create <vm name> on <" + '|'.join(CLOUDS) + "|all>\n"
                        "• list <" + '|'.join(CLOUDS) + "|all>\n"
                        "• delete <vm name> on <" + '|'.join(CLOUDS) + "|all>\n",
                "mrkdwn_in": [
                    "text"
                ],
                "color": "danger"
            }
        ]
    }
    resp = requests.post(payload["response_url"], json=response)
    print("response[%s]: %s" % (resp.status_code, resp.text))


def send_command(token, url, command, cloud, name=''):
    """Sends a command to cloud handlers. supported commands: create, list, delete"""

    payload = {
        "blocking": True,
        "input": {
            "name": name,
            "command": command
        },
        "secrets": [cloud]
    }
    print("%s/v1/runs?functionName=%s" % (url, cloud))
    print(payload)

    return requests.post("%s/v1/runs?functionName=%s" % (url, cloud),
                         headers={"Authorization": "Bearer %s" % token, "X-Dispatch-Org": "dispatch"},
                         json=payload)


def create_vm(secrets, response_url, name, cloud):
    """Creates a vm on a selected cloud and handles the response"""

    resp = send_command(secrets['jwt'], secrets['url'], 'create', cloud, name)

    if resp.status_code == 200:
        response = {
            "response_type": "in_channel",
            "attachments": [
                {
                    "title": "Create VM",
                    "text": "VM creation on {} in progress".format(cloud),
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
                    "text": "VM creation on {} failed: [{}] {}".format(cloud, resp.status_code, resp.text),
                    "mrkdwn_in": [
                        "text"
                    ],
                    "color": "danger"
                }
            ]
        }
    resp = requests.post(response_url, json=response)
    print("response[%s]: %s" % (resp.status_code, resp.text))


def delete_vm(secrets, response_url, name, cloud):
    """Deletes a vm on a selected cloud and handles the response"""

    resp = send_command(secrets['jwt'], secrets['url'], 'delete', cloud, name)

    if resp.status_code == 200:
        response = {
            "response_type": "in_channel",
            "attachments": [
                {
                    "title": "Delete VM",
                    "text": "VM deletion on {} in progress".format(cloud),
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
                    "title": "Delete VM",
                    "text": "VM deletion on {} failed: [{}] {}".format(cloud, resp.status_code, resp.text),
                    "mrkdwn_in": [
                        "text"
                    ],
                    "color": "danger"
                }
            ]
        }
    resp = requests.post(response_url, json=response)
    print("response[%s]: %s" % (resp.status_code, resp.text))


def list_vm(secrets, response_url, cloud):
    """List vms on a selected cloud and handles the response"""

    resp = send_command(secrets['jwt'], secrets['url'], 'list', cloud)
    vms = resp.json()['output']

    if len(vms) == 0:
        response = {
            "response_type": "in_channel",
            "attachments": [
                {
                    "title": "Instances in cloud {}".format(cloud),
                    "text": "No instances",
                    "mrkdwn_in": [
                        "text"
                    ],
                    "color": "good"
                }
            ]
        }
    else:
        text = "```NAME\tSTATUS\n"
        for vm in vms:
            text += "{}\t{}\n".format(vm['name'], vm['status'])
        text += "```"
        response = {
            "response_type": "in_channel",
            "attachments": [
                {
                    "title": "Instances in cloud {}".format(cloud.upper()),
                    "text": text,
                    "mrkdwn_in": [
                        "text"
                    ],
                    "color": "good"
                }
            ]
        }

    resp = requests.post(response_url, json=response)
    print("response[%s]: %s" % (resp.status_code, resp.text))


def create(secrets, payload):
    """handles the create command provided to cloudmaster"""

    r = re.compile(r"^(?P<command>create)\s(?P<name>.+)\s(on)\s(?P<cloud>.+)\s*$")
    m = r.match(payload["text"])
    if not m:
        return i_dont_understand(payload)

    params = m.groupdict()
    name = params['name']
    cloud = params['cloud']
    if cloud not in ['all'] + CLOUDS:
        return i_dont_understand(payload)

    if cloud == 'all':
        for c in CLOUDS:
            create_vm(secrets, payload['response_url'], name, c)
    else:
        create_vm(secrets, payload['response_url'], name, cloud)


def list_instances(secrets, payload):
    """Handles the list command provided to cloudmaster"""

    r = re.compile(r"^(?P<command>list)\s(?P<cloud>.+)\s*$")
    m = r.match(payload["text"])
    if not m:
        return i_dont_understand(payload)

    params = m.groupdict()
    cloud = params['cloud']

    if cloud not in ['all'] + CLOUDS:
        return i_dont_understand(payload)

    if cloud == 'all':
        for c in CLOUDS:
            list_vm(secrets, payload['response_url'], c)
    else:
        list_vm(secrets, payload['response_url'], cloud)


def delete(secrets, payload):
    """Handles the delete command provided to cloudmaster"""

    r = re.compile(r"^(?P<command>delete)\s(?P<name>.+)\s(on)\s(?P<cloud>.+)\s*$")
    m = r.match(payload["text"])
    if not m:
        return i_dont_understand(payload)

    params = m.groupdict()
    name = params['name']
    cloud = params['cloud']
    if cloud not in ['all'] + CLOUDS:
        return i_dont_understand(payload)

    if cloud == 'all':
        for c in CLOUDS:
            delete_vm(secrets, payload['response_url'], name, c)
    else:
        delete_vm(secrets, payload['response_url'], name, cloud)


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
        headers={"Authorization": "Bearer %s" % secrets["jwt"], "X-Dispatch-Org": "dispatch"},
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
        "list": list_instances,
        "delete": delete,
        "echo": echo
    }

    command = commands.get(command_name)
    if command is None:
        i_dont_understand(payload)
    else:
        command(ctx["secrets"], payload)
    return {"text": "ok"}