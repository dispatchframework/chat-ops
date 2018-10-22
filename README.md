# Chat-ops Dispatch demo

This guide walks through creation of a chat-ops integration with Slack using Dispatch.  Specifically we will be creating
slack commands for interacting with different clouds.

## Create Slack Incoming Webhook

The incoming webhook will be used to asynchronously post status updates to a particular slack channel.  The
setup is pretty straightforward.

[https://api.slack.com/incoming-webhooks](https://api.slack.com/incoming-webhooks)

Select a channel to post messages to.  Then record the webhook URL.  We will use this shortly.

## Create Slack Slash Command

Next we use a slack slash comand to issue "cloudmaster" commands.  Setup again should be pretty straightforward.

[https://api.slack.com/slash-commands](https://api.slack.com/slash-commands)

This demo assumes that the command is `/cloudmaster`.  The URL is the Dispatch API gateway hostname or IP address plus
the path of the API endpoint we will create later.  For internal integrations, certificates are not required (See
[Appendix](#appendix-using-lets-encrypt-with-dispatch) to find out how to use Let's Encrypt with Dispatch).
It should look something like `https://api-dispatch.example.com/cloudmaster`.  Also for method, choose `POST`.  The
rest of the configuration is mostly informational.  Configure as you like.

Store the URL from the incoming web hook in `slack.json`:

```json
{
  "statusUrl": "https://hooks.slack.com/services/********"
}
```

Now, let's go ahead and store the secret in Dispatch:

```
dispatch create secret slack slack.json
```

## Creating secrets
Our demo will use credentials for different clouds. Dispatch uses secrets to store them separately from your code, and injects them
when the function is executed. We need to create following secrets for this demo (if you are not using all the clouds, skip the respective secrets):

#### Cloudmaster
This is a secret that will be used to inject URL of Dispatch server to our functions, so that they can call subsequent functions as well.
Create a JSON file `cloudmaster.json` with following contents:
```json
{
  "url": "http://dispatch.example.com:8080"
}
```
Replace `dispatch.example.com:8080` with host and port of your dispatch-server installation. it should be resolvable inside the container
running the function. 

#### AWS
Create a JSON file `aws.json` with following contents:
```json
{
  "access_key": "<access_key>",
  "secret_key": "<secret_key>",
  "region": "us-west-2"
}
```
adjust the values to your environment. Then run:
```bash
dispatch create secret aws aws.json
```

#### Azure
Create a JSON file `azure.json` with following contents:
```json
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
```
adjust the values to your environment. Then run: 
```bash
dispatch create secret azure azure.json
```

#### GCP
Create a JSON file `gcp.json` with following contents:
```json
  "type": "service_account",
  "project_id": "<project_id>",
  ... Other service account credentials, as included in the JSON file downloaded from GCP IAM.
  "zone": "us-west1-c"
```
adjust the values to your environment. Then run: 
```bash
dispatch create secret gcp gcp.json
```

#### vSphere
Create a JSON file `vsphere.json` with following contents:
```json
{
  "host": "vCenter URL",
  "datacenter": "SDDC-Datacenter",
  "resourcePool": "Compute-ResourcePool",
  "vmFolder": "Workloads",
  "username": "<username>",
  "password": "<password>"
}
```
adjust the values to your environment. Then run: 
```bash
dispatch create secret vsphere vsphere.json
```

## Creating seed images
Dispatch comes with few images that are pre-configured for most common use cases. Base Images bring support for different
programming languages, where as Images build upon them, adding system and runtime dependencies. Run
```bash
dispatch create seed-images
```

to create images for python, java, nodejs and powershell. We will utilize those images below.


## Creating resources
This demo is using multiple resources. You can create them individually (for example, if you are not using one of the clouds).
If you want to create all of them, run `dispatch create -f all-resources.yaml`. This will create all base images, images,
functions, API definitions, event drivers and subscriptions used in the demo.

## Check the Slash Command Payload

This step is purely optional, but it's a good way of using a function (echo) to validate the payload information passed
to a function.  This is helpful when dealing with 3rd party services which may or may not have good API documentation.

Use an echo function to verify the slash command payload.

```
dispatch create api echo echo --path /cloudmaster --method POST --https-only
```

Execute the slash command

```
/cloudmaster create myvm on aws
```

If successful, you should see a nice little reply in slack.  However what we really are after is the full function
result.  The below command (without a run ID) will print the results of ALL echo runs.  You may want to omit the
`--json` flag to get a list of all the runs first... then pick the latest one.

```
dispatch get runs echo [run ID] --json
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

Since we're done with this, let's delete our API endpoint we are going to assign a new api to the same path later:

```
dispatch delete api echo
```

## Create some VMs!

We are now ready to create VMs.  If everything is correct creating a vm on GCP is a simple as:

```
/cloudmaster create vmtest01 on gcp
```

![success](success.png)

## What's next?

This should be a good introduction into a chat-ops workflow.  This example could be extended in a lot of different
ways to add new commands and functionality.


### Appendix: Using Let's encrypt with Dispatch

If you would like to use properly signed certificate with Dispatch, you can do that using `certbot`. Install certbot
using [official instructions](https://certbot.eff.org/docs/install.html), and then run:

```
certbot certonly --standalone -d dispatch.example.com
```
to obtain the certificate. Then run dispatch server using following flags:

```
--enable-tls --tls-certificate /etc/letsencrypt/live/dispatch.example.com/fullchain.pem --tls-certificate-key /etc/letsencrypt/live/dispatch.example.com/privkey.pem
```

In both commands replace `dispatch.example.com` with your domain.