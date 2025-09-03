#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

# Setup noVNC website
pushd "$(mktemp -d)"
public_folder_path="${PWD}/public"
cp -fr /usr/share/novnc "$public_folder_path"
cat <<'NOVNC_INDEX_HTML' >"${public_folder_path}/index.html"
<!doctype html>
<html lang="en">
<head>
<title>Loading ...</title>
<meta http-equiv="refresh" content="0; url=vnc.html?compression=0&quality=9&resize=remote&autoconnect=true">
</head>
<body style="color: lightgray; background-color: darkgray;">
<p>Loading ...</p>
</body>
</html>
NOVNC_INDEX_HTML

if ! nc -4z 127.0.0.1 5900; then
  pkill websockify || true
  rm -fr /tmp/.X11-unix
  vncserver :0 -localhost -SecurityTypes None -geometry 1024x768 -depth 24
fi

if ! timeout 10 sh -c "until nc -4z 127.0.0.1 5900; do sleep 0.1; done"; then
  echo "VNC server failed to bind 127.0.0.1:5900"
  exit 1
fi

if ! curl --fail-with-body --verbose http://127.0.0.1:6801; then
  pkill websockify || true
  websockify --daemon --wrap-mode=respawn --heartbeat=1 --web="$public_folder_path" 127.0.0.1:6801 127.0.0.1:5900
fi

if ! timeout 10 sh -c "until curl --fail-with-body --verbose http://127.0.0.1:6801; do sleep 0.1; done"; then
  echo "noVNC websockify web server failed to bind 127.0.0.1:6801"
  exit 1
fi
