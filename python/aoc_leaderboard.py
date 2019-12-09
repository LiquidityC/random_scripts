#!/usr/bin/env python

import os
import sys
import requests

if not "AOC_LB_URL" in os.environ:
    print("Invalid env[AOC_LB_URL]")
    sys.exit(1)

if not "AOC_SESSION_COOKIE" in os.environ:
    print("Invalid env[AOC_SESSION_COOKIE]")
    sys.exit(1)

url = os.environ["AOC_LB_URL"]
cookies = dict(session=os.environ["AOC_SESSION_COOKIE"])
with requests.get(url, cookies=cookies) as response:
    if response.status_code != 200:
        print("Bad response: %d" % response.status_code)
        sys.exit(1)

    jsonData = response.json()
    users = sorted([ u for u in jsonData["members"].values() ], key=lambda u: u["local_score"])
    users.reverse()
    for user in users:
        print("%s:\t%s\t%s" %
                (
                    str(user["local_score"]).rjust(5),
                    str(user["stars"]).rjust(2),
                    user["name"])
                )
