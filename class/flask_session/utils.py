import os
import subprocess
import shutil
import re
from typing import Tuple, Optional


def check_flask_sqlalchemy_version()-> bool:
    flask_sqlalchemy_version = (1, 0, 0)
    lib_path = "/www/server/panel/pyenv/lib/python3.7/site-packages/"

    flask_sqlalchemy_path_list = []
    try:
        for i in os.listdir(lib_path):
            path = os.path.join(lib_path, i)
            if not os.path.isdir(path):
                continue
            name = i.lower()
            if name.startswith("flask_sqlalchemy-") or name == "flask_sqlalchemy":
                flask_sqlalchemy_path_list.append(path)
            if name == "flask_sqlalchemy":
                file = os.path.join(path, "__init__.py")
                if not os.path.isfile(file):
                    continue
                with open(file, "r") as f:
                    for line in f:
                        if line.startswith("__version__"):
                            ver = re.search(r"(\d+\.\d+(\.\d+)?)", line).group()
                            ver_list = ver.split(".")
                            if len(ver_list) < 3:
                                for _ in range(3 - len(ver_list)):
                                    ver_list.append("0")
                            flask_sqlalchemy_version = tuple(int(i) for i in ver_list)

    except:
        import traceback
        print(traceback.format_exc(), flush=True)
        pass

    pip_bin = "/www/server/panel/pyenv/bin/pip"
    if flask_sqlalchemy_version != (2, 5, 1):
        try:
            if flask_sqlalchemy_path_list:
                for path in flask_sqlalchemy_path_list:
                    shutil.rmtree(path)
            subprocess.call(
                "{pip_bin} install Flask-SQLAlchemy==2.5.1 SQLAlchemy==1.3.24".format(pip_bin=pip_bin),
                shell=True
            )
        except:
            import traceback
            print(traceback.format_exc(), flush=True)
            return False

    return True
