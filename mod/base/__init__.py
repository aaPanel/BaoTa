import json
import time
from typing import Dict, List, Tuple, Union

from .process import RealProcess, Process
from .process import RealUser, User
from .process import RealServer, Server


def json_response(
        status: bool,
        msg: str = None,
        data: Union[Dict, List, Tuple, bool, str, int, float] = None,
        code: int = 0,
        args: Union[List[str], Tuple[str]] = None,
):
    if isinstance(msg, str) and args is not None:
        for i in range(len(args)):
            rep = '{' + str(i + 1) + '}'
            msg = msg.replace(rep, args[i])

    if msg is None:
        msg = "ok"

    return {
        "status": status,
        "msg": msg,
        "data": data,
        "code": code,
        "timestamp": int(time.time())
    }


def list_args(get, key) -> list:
    list_str = get.get(key, "")
    if not list_str:
        return []
    if isinstance(list_str, (list, tuple)):
        return list(list_str)
    if not isinstance(list_str, str):
        return []
    list_str = list_str.strip()
    if list_str.startswith("[") and list_str.endswith("]"):
        try:
            res = json.loads(list_str)
        except:
            return []
    else:
        res = [i for i in list_str.split(",") if i]
    return  res

