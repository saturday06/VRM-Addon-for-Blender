#!/bin/bash
# SPDX-License-Identifier: MIT OR GPL-3.0-or-later

set -eu -o pipefail

cd "$(dirname "$0")/.."

./tools/devcontainer_create_venv.sh

# Refreshing repository
# https://git-scm.com/docs/git-status#_background_refresh
git status --short

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

vncserver -list -cleanstale
rm -fr /tmp/.X11-unix/

# Start daemon
mkdir -p "$HOME/.local/supervisord/logs"
cat >"$HOME/.local/supervisord/supervisord.conf" <<'SUPERVISORD_CONF'
[unix_http_server]
file=%(ENV_HOME)s/.local/supervisord/supervisord.sock

[supervisord]
logfile=%(ENV_HOME)s/.local/supervisord/logs/supervisord.log
pidfile=%(ENV_HOME)s/.local/supervisord/supervisord.pid
childlogdir=%(ENV_HOME)s/.local/supervisord/logs
nocleanup=true

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix://%(ENV_HOME)s/.local/supervisord/supervisord.sock

[program:vncserver]
command=/usr/bin/vncserver :0 -useold -rfbunixpath /tmp/vnc0.sock -localhost -SecurityTypes None -geometry 1024x768 -depth 24

[program:websockify]
command=/usr/bin/websockify --unix-target=/tmp/vnc0.sock --web=/workspace/.cache/novnc 127.0.0.1:6801
SUPERVISORD_CONF

if [ -f "$HOME/.local/supervisord/supervisord.pid" ]; then
  # TODO: No kill. Reload.
  supervisord_pid=$(cat "$HOME/.local/supervisord/supervisord.pid")
  kill "$supervisord_pid" || true
  if ! timeout 10 sh -c "while kill -0 '$supervisord_pid'; do sleep 1 done"; then
    kill -9 "$supervisord_pid" || true
  fi
  rm "$HOME/.local/supervisord/supervisord.pid"
fi
supervisord -c "$HOME/.local/supervisord/supervisord.conf"

if ! timeout 10 sh -c "until nc -4z 127.0.0.1 5900; do sleep 0.1; done"; then
  echo "VNC server failed to bind 127.0.0.1:5900"
  exit 1
fi

if ! timeout 10 sh -c "until nc -Uz /tmp/vnc0.sock; do sleep 0.1; done"; then
  echo "VNC server failed to listen /tmp/vnc0.sock"
  exit 1
fi

if ! timeout 10 sh -c "until nc -4z 127.0.0.1 6801; do sleep 0.1; done"; then
  echo "noVNC server failed to bind 127.0.0.1:6801"
  exit 1
fi
