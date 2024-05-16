#!/bin/bash

if [ $# -eq 0 ]; then
    pkill -f 'ssh -D 8100'
    ssh -D 8100 -nNT csjumphost
else
    pkill -f 'ssh -D 8101'
    ssh -D 8101 -nNT "$1"
fi