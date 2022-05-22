#!/bin/bash

set -eux -o pipefail
shellcheck "$0"

date > /root/tests/timestamp.txt

(set +e; (while true; do Xvfb :0 -screen 0 1600x900x24 -fbdir "$(mktemp -d)"; done) 2>&1 | tee logs/Xvfb.log) &
sleep 1

fvwm &
sleep 1

if [ "$CI" = "true" ]; then
  sleep 10800
  exit 1
fi

(set +e; (while true; do x11vnc -display "$DISPLAY" -forever; done) 2>&1 | tee logs/x11vnc.log) &
sleep 1

gnome-terminal "--display=$DISPLAY" &
sleep 1

set +e
(while true; do /root/noVNC/utils/novnc_proxy --listen 6080 --vnc localhost:5900; done) 2>&1 | tee logs/noVNC.log
