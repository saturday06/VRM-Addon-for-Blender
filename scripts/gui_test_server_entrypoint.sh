#!/bin/bash

set -eux -o pipefail

(
  set +e
  (while true; do Xvfb :0 -screen 0 1600x900x24 -fbdir "$(mktemp -d)"; done) 2>&1 | tee var/log/Xvfb.log
) &
timeout 5 sh -c "until glxinfo > /dev/null; do sleep 0.1; done"

fvwm >var/log/fvwm.log 2>&1 &

if [ "$(uname -m)" = "aarch64" ] && ! java -jar sikulixide.jar -c -r tests/test.sikuli; then
  rm /root/.Sikulix/SikulixLibs/libopencv_java430.so
  ln -s /usr/lib/jni/libopencv_java451.so /root/.Sikulix/SikulixLibs/libopencv_java430.so
  rm /root/.Sikulix/SikulixLibs/libJXGrabKey.so
  ln -s /usr/lib/aarch64-linux-gnu/jni/libJXGrabKey.so /root/.Sikulix/SikulixLibs/libJXGrabKey.so
fi

if [ "$CI" = "true" ]; then
  sleep 10800
  exit 1
fi

(
  set +e
  (while true; do x11vnc -display "$DISPLAY" -forever; done) 2>&1 | tee var/log/x11vnc.log
) &
timeout 5 sh -c "until nc -z 127.0.0.1 5900; do sleep 0.1; done"

lxterminal >var/log/lxterminal.log 2>&1 &

set +e
(while true; do /root/noVNC/utils/novnc_proxy --listen 6080 --vnc 127.0.0.1:5900; done) 2>&1 | tee var/log/noVNC.log
