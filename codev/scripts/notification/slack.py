#!/usr/bin/env python3

# https://api.slack.com/incoming-webhooks

import sys
import json
from urllib.request import urlopen
from urllib.parse import parse_qs, urlencode


def send_message(message, color, url, channel, username, project, environment, configuration, source, icon):
    format_vars = dict(
        project=project,
        environment=environment,
        configuration=configuration,
        source=source
    )
    data = {
        'channel': channel.format(**format_vars),
        'username': username.format(**format_vars),
        "icon_emoji": icon,
        "attachments": [
            {
                "pretext": message.format(**format_vars) if message else '',
                "color": color,
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
                        "title": "Configuration",
                        "value": configuration,
                        "short": True
                    },
                    {
                        "title": "Source",
                        "value": source,
                        "short": True
                    },
                ],
                "mrkdwn_in": ["pretext", ]
            }
        ]
    }
    urlopen(
        url,
        data=urlencode(
            dict(
                payload=json.dumps(data)
            )
        ).encode()
    )


if __name__ == "__main__":

    stdin = parse_qs(sys.stdin.read())
    project = stdin.get('project', [''])[0]
    environment = stdin.get('environment', [''])[0]
    configuration = stdin.get('configuration', [''])[0]
    source = stdin.get('source_transition', [''])[0]

    url = stdin.get('url', [''])[0]
    channel = stdin.get('channel', [''])[0]
    username = stdin.get('username', ['{project} bot'])[0]
    message = stdin.get('message', [''])[0]
    icon = stdin.get('icon', [':ghost:'])[0]
    color = stdin.get('color', ['good'])[0]

    send_message(message, color, url, channel, username, project, environment, configuration, source, icon)
