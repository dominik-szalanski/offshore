#!/bin/bash

if [ $# -eq 0 ]; then
    echo "need parameter"
    exit 1
fi

case $1 in
    office)
        xrandr --output eDP --mode 2560x1600 --pos 0x377 --rotate normal --rate 165 --output DisplayPort-1 --primary --mode 3440x1440 --pos 2560x0 --rotate normal --rate 100
        exit 0
        ;;
    wfh)
        xrandr --output DisplayPort-3 --mode 3840x2160 --primary --rate 60 --output eDP --off
        exit 0
        ;;
    *)
        echo "unknown parameter"
        exit 1
        ;;
esac