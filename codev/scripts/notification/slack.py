#!/usr/bin/env python3

# https://api.slack.com/incoming-webhooks

import sys
import json
from urllib.request import urlopen
from urllib.parse import parse_qs, urlencode


def send_message(
    message, color, url, channel, username, project, environment, configuration, source, source_options, icon
):
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
                        "value": '{source}:{source_options}'.format(source=source, source_options=source_options),
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
        source = isolation.get('current_source')
        source_options = isolation.get('current_source_options')
    else:
        source = arguments.get('source')
        source_options = isolation.get('source_options')

    url = arguments.get('url', '')
    channel = arguments.get('channel', '')
    username = arguments.get('username', '{project} bot')
    message = arguments.get('message', '')
    icon = arguments.get('icon', ':ghost:')
    color = arguments.get('color', 'good')

    send_message(
        message, color, url, channel, username, project, environment, configuration, source, source_options, icon
    )
