# Radio Dispatch Demo

## Create Slack Slash Command

Configure the [/cloudmaster slash command](https://example.slack.com/services/*********)

- Set the URL approprately

Store the token in `slack.json`:

```json
{
  "token": "*********"
}
```

## Check the Slash Command Payload

Use an echo function to verify the slash command payload.

```
dispatch create function nodejs6 echo echo.js
dispatch create api echo echo --path /cloudmaster --method POST --https-only
```

Execute the slash command
```
/cloudmaster create vm on prod
```

Get the function result
```
dispatch get runs echo --json
{
    ...
    "output": {
        "channel_id": "********",
        "channel_name": "privategroup",
        "command": "/cloudmaster",
        "context": {
            "httpContext": {
                "accept": "application/json,*/*",
                "accept-encoding": "gzip,deflate",
                "args": "functionName=echo",
                "content-length": "340",
                "content-type": "application/x-www-form-urlencoded",
                "cookie": "cookie",
                "host": "*********.example.com",
                "method": "POST",
                "request": "POST /cloudmaster HTTP/1.1",
                "request-uri": "/cloudmaster",
                "scheme": "https",
                "server-protocol": "HTTP/1.1",
                "upstream-uri": "/v1/runs",
                "uri": "/cloudmaster",
                "user-agent": "Slackbot 1.0 (+https://api.slack.com/robots)"
            },
            "secrets": {},
            "serviceBindings": {}
        },
        "enterprise_id": "********",
        "enterprise_name": "Example.com",
        "response_url": "https://hooks.slack.com/commands/********",
        "team_domain": "example",
        "team_id": "********",
        "text": "echo",
        "token": "********",
        "user_id": "********",
        "user_name": "********"
    },
    ...
}
```

## Create a Service Account on Dispatch

In order to call the Dispatch API from within a function, we need a service account:

```
dispatch iam create serviceaccount radio-demo --public-key ./radio.pub
dispatch iam create policy all-access --subject radio-demo --action "*" --resource "*" --service-account radio-demo
```

We are going to generate a JWT and store as a secret which the function can use:

```
python gen_jwt.py radio-demo ./radio.key 30
Dispatch secret radio-demo.json
```

Store the secrets to be used by dispatch:

```
dispatch create secret radio-demo radio-demo.json
```

## Register the Cloudmaster Function

Create the `slack` secret which contains the token and incoming web-hook url (used later):

```json
{
  "token": "*********",
  "statusUrl": "https://hooks.slack.com/services/********"
}
```

```
dispatch create secret slack slack.json
```

The cloudmaster function is a router to sub-functions which do the work according to the command.

```
dispatch create function python3 cloudmaster cloudmaster.py --secret radio-demo --secret slack
```

Create the /cloudmaster API endpoint:

```
dispatch create api cloudmaster cloudmaster --path /cloudmaster --method POST --https-only
```

Update the [/cloudmaster slash command](https://example.slack.com/services/********) to point to our new endpoint.

Validate the echo command through cloudmaster.

```
slack: /cloudmaster echo hello radio
```

## Register the Clone VM Function

Create the `vcenter` secret which contains the credentials to vCenter running on VMC

```json
{
  "host": "vcenter.********.vmc.vmware.com",
  "datacenter": "SDDC-Datacenter",
  "resourcePool": "Compute-ResourcePool",
  "vmFolder": "Workloads",
  "username": "********@vmc.local",
  "password": "********",
  "vcenterurl": "********@vmc.local:********@vcenter.********.vmc.vmware.com:443"
}
```

```
dispatch create secret vcenter ./vcenter.json
```

```
dispatch create function python3-pyvmomi clone-vm clonevm.py --secret vcenter
```

## Create a vCenter Event Driver

```
dispatch create eventdriver vcenter --name vcenter --secret vcenter
```

## Subscribe to vCenter Events

Create a `status` function which will update a slack channel with vCenter events:

```
dispatch create function python3-pyvmomi status status.py
```