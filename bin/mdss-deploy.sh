#!/usr/bin/env bash

filelocation=${1:-none}

if [ ! -f $filelocation ]; then
    echo "File not found!"
    exit 1
fi

for dir in {1..12}; do for folder in $(ssh "mdss-$dir" "ls -d */"); do echo "Uploading to mdss-$dir:$folder" && scp "$filelocation" "mdss-$dir:$folder" && ssh "mdss-$dir" "./service_control.sh $folder restart" ; done; done

