import requests
import json

message = "My birthday was last week and I went to London Zoo"


def get_econtext_data(message):

    api_url = 'https://api.econtext.com/v2/classify/social'
    username = '' # add own eContext creds
    password = '' # add own eContext creds

    body = '{"social":["' + message + '"], "async": false}'
    headers = {"content-type": "application/json"}
    r = requests.post(api_url, data=body, auth=(username, password), headers=headers)
    json_data = r.json()
    print json_data

    return json_data


get_econtext_data(message)