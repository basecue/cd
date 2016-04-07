#!/usr/bin/env python3

import sys
import requests
from urllib.parse import parse_qs


def send_message(message, url, channel, user, project, environment, infrastructure, installation, icon):
    data = {
        'channel': "#{channel}".format(chennel=channel),
        'username': user,
        "icon_emoji": icon,
        "attachments": [
            {
                "pretext": message.format(
                    project=project,
                    environment=environment,
                    infrastructure=infrastructure,
                    installation=installation
                ),
                "color": "good",
                "fields": [
                    {
                        "title": "Project",
                        "value": project.capitalize(),
                        "short": True
                    },
                    {
                        "title": "Environment",
                        "value": environment,
                        "short": True
                    },
                    {
                        "title": "Infrastructure",
                        "value": infrastructure,
                        "short": True
                    },
                    {
                        "title": "Installation",
                        "value": installation,
                        "short": True
                    },
                ],
                "mrkdwn_in": ["pretext", ]
            }
        ]
    }
    requests.post(url, json=data)


if __name__ == "__main__":

    stdin = parse_qs(sys.stdin.read())
    project = stdin.get('project', [''])[0]
    environment = stdin.get('environment', [''])[0]
    infrastructure = stdin.get('infrastructure', [''])[0]
    installation = stdin.get('installation_transition', [''])[0]

    args = sys.argv()
    url = args[0]
    channel = args[1]
    user = args[2]
    message = args[3]
    icon = args[4]

    send_message(message, url, channel, user, project, environment, infrastructure, installation, icon)
