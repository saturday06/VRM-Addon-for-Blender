#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

# Setup noVNC website
rm -fr /workspace/.cache/novnc
cp -fr /usr/share/novnc /workspace/.cache/
cat <<'NOVNC_INDEX_HTML' >/workspace/.cache/novnc/index.html
<html lang="en">
<head>
<title>Loading ...</title>
<meta http-equiv="refresh" content="0; url=vnc.html?compression=0&quality=9&resize=remote&autoconnect=true" />
<style>
body {
  color: lightgray;
  background-color: darkgray;
}
</style>
</head>
<body>
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

if ! curl --fail --silent http://127.0.0.1:6801; then
  pkill websockify || true
  websockify --daemon --wrap-mode=respawn --heartbeat=1 --web=/workspace/.cache/novnc 127.0.0.1:6801 127.0.0.1:5900
fi

./tools/devcontainer_create_venv.sh

# Refreshing repository
# https://git-scm.com/docs/git-status#_background_refresh
git status --short
