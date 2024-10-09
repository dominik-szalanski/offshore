#!/bin/bash

if [ $# -eq 0 ]; then
    echo "loading my private key"
    ssh-add ~/.ssh/id_ed25519_ds_cs
    ssh-add ~/.ssh/id_ed25519_cs_global
    exit 0
fi

case $1 in
    cs)
        ssh-add ~/.keys/cs_*
        exit 0
        ;;
    james)
        ssh-add ~/.keys/james_*
        exit 0
        ;;
    fingolfin)
        ssh-add ~/.keys/fingolfin_*
        exit 0
        ;;    
    bellsize)
        ssh-add ~/.keys/bellsizeGrovePartners_*
        exit 0
        ;;
    marvel)
        ssh-add ~/.keys/marvel_*
        exit 0
        ;;
    primrose)
        ssh-add ~/.keys/primrose_*
        exit 0
        ;;
    infinity)
        ssh-add ~/.keys/infinity-research*
        exit 0
	    ;;
    flintstone)
        ssh-add ~/.keys/flintstone_*
        exit 0
	    ;;
    ecn)
        ssh-add ~/.keys/ecn_*
        exit 0
	    ;;
    coober)
        ssh-add ~/.keys/coober_*
        exit 0
	    ;;
    arpara)
        ssh-add ~/.keys/arpara_*
        exit 0
	    ;;
    *)
        echo "unknown parameter"
        exit 1
        ;;
esac
