#!/usr/bin/env python3

REQUIRES = ['requests']

import sys
import requests
from urllib.parse import parse_qs


def send_message(message, url, channel, username, project, environment, infrastructure, installation, icon):
    data = {
        'channel': channel,
        'username': username.format(
            project=project,
            environment=environment,
            infrastructure=infrastructure,
            installation=installation
        ),
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
                        "value": project,
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

    url = stdin.get('url', [''])[0]
    channel = stdin.get('channel', [''])[0]
    username = stdin.get('username', ['{project} bot'])[0]
    message = stdin.get('message', ['Project *{project}* has been installed to environment *{environment}* with infrastructure *{infrastructure}* at installation *{installation}*.'])[0]
    icon = stdin.get('icon', [':ghost:'])[0]

    send_message(message, url, channel, username, project, environment, infrastructure, installation, icon)
