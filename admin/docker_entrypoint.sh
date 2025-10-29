#!/usr/bin/env bash
set -e

export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"

export NOX_ENV_DIR="/gcovr/.nox-containerized/$(lsb_release -s -r).uid_$(id -u)"
export XDG_CACHE_HOME="$NOX_ENV_DIR/.cache"

# Run command with ${DOCKER_ENTRYPOINT} if the first argument is empty, contains a "-" or is not a system command.
# The last part inside the "{}" is a workaround for the following bug in ash/dash:
#   https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=874264
if [ -z "${1}" ] || [ "${1#-}" != "${1}" ] || [ -z "$(command -v "${1}")" ] || { [ -f "${1}" ] && ! [ -x "${1}" ]; }; then
  set -- python3 -m nox --envdir $NOX_ENV_DIR "$@"
fi

exec "$@"
