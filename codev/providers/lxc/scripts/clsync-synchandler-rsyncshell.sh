#!/bin/sh

from="`pwd`"

action="$1"
label="$2"
files="$3"
exclude="$4"


excludefrom=''
if [ "$exclude" != "" ]; then
    excludefrom="--exclude-from=${exclude}"
fi

rsync -avH --delete-before "$excludefrom" --include-from="${files}" --exclude='*' "$from"/ "$TO"/ > /dev/null
