#!/bin/bash

if [ $# -eq 0 ]; then
    echo "need parameter"
    exit 1
fi

case $1 in
    office)
        xrandr --output eDP-1 --mode 2560x1600 --pos 0x377 --rotate normal --rate 165 --output DisplayPort-1-0 --primary --mode 3440x1440 --pos 2560x0 --rotate normal --rate 100
        ;;
    wfh)
        xrandr --output DisplayPort-1-0 --mode 3840x2160 --primary --rate 120 --output eDP-1 --off
        ;;
    *)
        echo "unknown parameter"
        exit 1
        ;;
esac
feh --bg-scale imgs/background.png
