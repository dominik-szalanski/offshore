#!/bin/bash

sudo ip route add local default dev lo table 100
sudo ip rule add fwmark '0x01' lookup 100
sudo ip -6 route add local default dev lo table 100
sudo ip -6 rule add fwmark '0x01' lookup 100

if [ $# -eq 0 ]; then
    sudo sshuttle --method tproxy -e 'ssh -i /home/ds/.ssh/id_ed25519_ds_cs -o "ControlMaster=auto" -o "ControlPath=/home/ds/.ssh/master-%r@%h:%p.socket"' -r ds@secure.cryptostruct.com -x 10.0.0.0/16 10.0.0.0/8 57.128.210.133/32 89.58.50.26/32
    exit 0
fi

case $1 in
    ar)
        sudo sshuttle --method tproxy -e 'ssh -i /home/ds/.ssh/id_ed25519_ds_cs' -r ds@jump-server.sswrockfunds.com -x 10.0.0.0/16 10.0.0.0/8
        exit 0
        ;;
    *)
        echo "unkown parameter"
        exit 1
        ;;
esac
