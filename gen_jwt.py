import json
import sys
import time

import jwt

if __name__ == "__main__":
    sa = sys.argv[1]
    private_key_path = sys.argv[2]
    ttl = int(sys.argv[3])
    host = sys.argv[4]

    with open(private_key_path) as fh:
        private = fh.read()

    encoded = jwt.encode(
        {
            "iss": "dispatch/" + sa,
            "exp": int(time.time()+ttl*86400),
            "iat": int(time.time())
        },
        bytes(private, "utf-8"),
        algorithm='RS256')

    with open("%s.json" % sa, "w") as fh:
        json.dump(
            {
                "jwt": encoded.decode("utf-8"),
                "url": "https://%s" % host
            }, fh)

    print("Dispatch secret %s.json" % sa)
