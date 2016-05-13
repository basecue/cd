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

    arguments = json.loads(sys.stdin.read())
    project = arguments.get('project', '')
    environment = arguments.get('environment', '')
    configuration = arguments.get('configuration', '')

    isolation = arguments.get('isolation', {})
    if isolation:
        source = isolation.get('current_source_ident')
    else:
        source = arguments.get('source_ident')

    url = arguments.get('url', '')
    channel = arguments.get('channel', '')
    username = arguments.get('username', '{project} bot')
    message = arguments.get('message', '')
    icon = arguments.get('icon', ':ghost:')
    color = arguments.get('color', 'good')

    send_message(message, color, url, channel, username, project, environment, configuration, source, icon)
