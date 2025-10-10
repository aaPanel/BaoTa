_BT_PYTHON_NAME_MAP_FILE="/www/server/panel/data/python_project_name2env.txt"

ACTIVATE_NAME="${1}"
if [ -z "${ACTIVATE_NAME}" ]; then
  echo "使用：\" source py-project-env <project_name> \"启动虚拟环境"
  echo "使用：\" bt_env_deactivate \"命令, 退出虚拟环境, 回到之前的环境"
  echo "（仅支持Linux服务器使用）"
  return 1
fi

_bt_map_safe_get() {
    awk -F: -v key="$1" '$1 == key {print $2; exit}' "${_BT_PYTHON_NAME_MAP_FILE}" 2>/dev/null
}

if [ -z "${_BT_PROJECT_ENV}"'' ]; then
  _BT_PROJECT_ENV="$(_bt_map_safe_get ${ACTIVATE_NAME})"
else
  ACTIVATE_NAME=$(basename "${_BT_PROJECT_ENV}")
fi

if [ ! -d "${_BT_PROJECT_ENV}" ]; then
  echo "项目名称为：${ACTIVATE_NAME} 的虚拟环境不存在"
  return 1
fi

# This file must be used with "source bin/activate" *from bash*
# You cannot run it directly

bt_env_deactivate () {
    # reset old environment variables
    if [ -n "${_OLD_VIRTUAL_PATH:-}" ] ; then
        PATH="${_OLD_VIRTUAL_PATH:-}"
        export PATH
        unset _OLD_VIRTUAL_PATH
    fi
    if [ -n "${_OLD_VIRTUAL_PYTHONHOME:-}" ] ; then
        PYTHONHOME="${_OLD_VIRTUAL_PYTHONHOME:-}"
        export PYTHONHOME
        unset _OLD_VIRTUAL_PYTHONHOME
    fi

    # This should detect bash and zsh, which have a hash command that must
    # be called to get it to forget past commands.  Without forgetting
    # past commands the $PATH changes we made may not be respected
    if [ -n "${BASH:-}" ] || [ -n "${ZSH_VERSION:-}" ] ; then
        hash -r 2> /dev/null
    fi

    if [ -n "${_OLD_VIRTUAL_PS1:-}" ] ; then
        PS1="${_OLD_VIRTUAL_PS1:-}"
        export PS1
        unset _OLD_VIRTUAL_PS1
    fi

    unset VIRTUAL_ENV
    unset VIRTUAL_ENV_PROMPT
    if [ ! "${1:-}" = "nondestructive" ] ; then
    # Self destruct!
        unset -f bt_env_deactivate
    fi
}

# unset irrelevant variables
bt_env_deactivate nondestructive

_OLD_VIRTUAL_PATH="$PATH"

if [ -d "${_BT_PROJECT_ENV}/bin" ] ; then
  VIRTUAL_ENV="${_BT_PROJECT_ENV}"
  PATH="$VIRTUAL_ENV/bin:$PATH"
else
  VIRTUAL_ENV="${_BT_PROJECT_ENV}"
  PATH="$VIRTUAL_ENV:$PATH"
fi

# use the path as-is
export VIRTUAL_ENV

export PATH

# unset PYTHONHOME if set
# this will fail if PYTHONHOME is set to the empty string (which is bad anyway)
# could use `if (set -u; : $PYTHONHOME) ;` in bash
if [ -n "${PYTHONHOME:-}" ] ; then
    _OLD_VIRTUAL_PYTHONHOME="${PYTHONHOME:-}"
    unset PYTHONHOME
fi

if [ -z "${VIRTUAL_ENV_DISABLE_PROMPT:-}" ] ; then
    _OLD_VIRTUAL_PS1="${PS1:-}"
    PS1="(${ACTIVATE_NAME}) ${PS1:-}"
    export PS1
    VIRTUAL_ENV_PROMPT="(${ACTIVATE_NAME}) "
    export VIRTUAL_ENV_PROMPT
fi

# This should detect bash and zsh, which have a hash command that must
# be called to get it to forget past commands.  Without forgetting
# past commands the $PATH changes we made may not be respected
if [ -n "${BASH:-}" ] || [ -n "${ZSH_VERSION:-}" ] ; then
    hash -r 2> /dev/null
fi
