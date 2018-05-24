import json
import requests

def handle(ctx, payload):
    secrets = ctx["secrets"]

    payload = json.loads(payload)

    msg = payload.get("message")
    metadata = payload.setdefault("metadata", {})
    print(metadata)

    resp = requests.post(secrets["statusUrl"], json={"text": msg})
    if not resp.ok:
        raise Exception("Post to slack failed[%s]: %s" % (resp.status_code, resp.text))
