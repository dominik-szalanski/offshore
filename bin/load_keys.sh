#!/bin/bash

if [ $# -eq 0 ]; then
    echo "loading my private key"
    ssh-add ~/.ssh/id_ed25519_ds_cs
    ssh-add ~/.ssh/id_ed25519_cs_global
    exit 0
else
    ssh-add ~/.keys/$1_*
fi

