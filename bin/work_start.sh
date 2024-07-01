#!/bin/bash

if [ $# -eq 0 ]; then
    echo "need parameter"
    exit 1
fi

load_keys.sh

socksproxy.sh

if [ "$1" != "none" ]; then
    x_setup.sh "$1"
fi

i3-msg "workspace 4; append_layout ~/work/repos/offshore/cfgs/ws/ws-3.cfg"
i3-msg "exec --no-startup-id chromium --profile-directory=Profile\ 1 --app-id=cifhbcnohmdccbgoicgdjpfamggdegmo"
i3-msg "exec --no-startup-id chromium --profile-directory=Profile\ 1 --app-id=faolnafnngnfdaknnbpnkhgohbobgegn"
i3-msg "exec --no-startup-id kuro"
i3-msg "exec --no-startup-id telegram-desktop"
i3-msg "exec --no-startup-id keeperpasswordmanager"
i3-msg "exec --no-startup-id urxvt"
i3-msg "exec --no-startup-id chromium --profile-directory=Profile\ 1"
i3-msg "exec --no-startup-id chromium --profile-directory=Profile\ 2"

i3-msg "workspace 5; append_layout ~/work/repos/offshore/cfgs/ws/ws-4.cfg"
i3-msg "exec --no-startup-id vscodium"
i3-msg "exec --no-startup-id urxvt"
