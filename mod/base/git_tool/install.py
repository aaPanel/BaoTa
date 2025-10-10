import re
from .util import ExecShell


def installed():
    sh_str = "git --version"
    out, error = ExecShell(sh_str)
    if re.search(r"git\s+version\s+(\d+\.){1,4}\d+", out):
        return True
    return False


def version_1_5_3() -> bool:
    sh_str = "git --version"
    out, error = ExecShell(sh_str)
    res = re.search(r"git\s+version\s+(?P<v>(\d+\.){1,4}\d+)", out)
    if not res:
        return False
    ver = [int(i) for i in res.group('v').split(".")]
    if len(ver) < 3:
        ver.extend([0] * (3 - len(ver)))
    if ver[0] > 1:
        return True
    elif ver[0] == 1 and ver[1] > 5:
        return True
    elif ver[0] == 1 and ver[1] == 5 and ver[3] >= 3:
        return True
    return False


def install_git():
    check_str = "Git installed successfully"
    if not installed():
        script_path = "/www/server/panel/mod/base/git_tool/install.sh"
        out, error = ExecShell("bash {}".format(script_path))
        if out.find(check_str) != -1:
            return True
        else:
            return False
    return True
