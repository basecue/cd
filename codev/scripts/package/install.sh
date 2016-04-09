#!/usr/bin/env bash

DEBIAN_FRONTEND=noninteractive apt-get install $@ -y --force-yes
