import json
import os
import sys
import traceback
from typing import Dict, Union

from .mods import TaskConfig, TaskTemplateConfig, TaskRecordConfig, SenderConfig, load_task_template_by_config, \
    load_task_template_by_file, UPDATE_MOD_PUSH_FILE, UPDATE_VERSION_FILE, PUSH_DATA_PATH
from .base_task import BaseTask, BaseTaskViewMsg
from .send_tool import WxAccountMsg, WxAccountLoginMsg, WxAccountMsgBase
from .system import PushSystem, get_push_public_data, push_by_task_keyword, push_by_task_id
from .manager import PushManager
from .util import read_file, write_file, debug_log, get_db_by_file, DB

__all__ = [
    "TaskConfig",
    "TaskTemplateConfig",
    "TaskRecordConfig",
    "SenderConfig",
    "BaseTaskViewMsg",
    "load_task_template_by_config",
    "load_task_template_by_file",
    "BaseTask",
    "WxAccountMsg",
    "WxAccountLoginMsg",
    "WxAccountMsgBase",
    "PushSystem",
    "get_push_public_data",
    "PushManager",
    "push_by_task_keyword",
    "push_by_task_id",
    "UPDATE_MOD_PUSH_FILE",
    "update_mod_push_system",
    "UPDATE_VERSION_FILE",
    "PUSH_DATA_PATH",
    "get_default_module_dict",
    'update_mod_push_system2',
]


def update_mod_push_system():
    if os.path.exists(UPDATE_MOD_PUSH_FILE):
        return

    # 只将已有的告警任务("site_push", "system_push", "database_push") 移动

    try:
        push_data = json.loads(read_file("/www/server/panel/class/push/push.json"))
    except:
        return

    if not isinstance(push_data, dict):
        return
    pmgr = PushManager()
    default_module_dict = get_default_module_dict()
    for key, value in push_data.items():
        if key == "site_push":
            _update_site_push(value, pmgr, default_module_dict)
        elif key == "system_push":
            _update_system_push(value, pmgr, default_module_dict)
        elif key == "database_push":
            _update_database_push(value, pmgr, default_module_dict)
        elif key == "rsync_push":
            _update_rsync_push(value, pmgr, default_module_dict)
        elif key == "load_balance_push":
            _update_load_push(value, pmgr, default_module_dict)
        elif key == "task_manager_push":
            _update_task_manager_push(value, pmgr, default_module_dict)

    write_file(UPDATE_MOD_PUSH_FILE, "")


def get_default_module_dict():
    from mod.base.msg import manager

    manager.SenderManager.sync_default_sender()
    res = {}
    wx_account_list = []
    for data in SenderConfig().config:
        if not data["used"]:
            continue
        if data.get("original", False):
            res[data["sender_type"]] = data["id"]

        if data["sender_type"] == "webhook":
            res[data["data"].get("title")] = data["id"]

        if data["sender_type"] == "wx_account":
            wx_account_list.append(data)

    wx_account_list.sort(key=lambda x: x.get("data", {}).get("create_time", ""))
    if wx_account_list:
        res["wx_account"] = wx_account_list[0]["id"]

    return res


def _update_site_push(old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
                      pmgr: PushManager,
                      df_mdl: Dict[str, str]):
    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        if v["type"] == "ssl":
            push_data = {
                "template_id": "1",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", "all"),
                        "cycle": v.get("cycle", 15)
                    },
                    "number_rule": {
                        "total": v.get("push_count", 1)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "site_endtime":
            push_data = {
                "template_id": "2",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 7)
                    },
                    "number_rule": {
                        "total": v.get("push_count", 1)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "panel_pwd_endtime":
            push_data = {
                "template_id": "3",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 15),
                        "interval": 600
                    },
                    "number_rule": {
                        "total": v.get("push_count", 1)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "ssh_login_error":
            push_data = {
                "template_id": "4",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 30),
                        "count": v.get("count", 3),
                        "interval": v.get("interval", 600)
                    },
                    "number_rule": {
                        "day_num": v.get("day_limit", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "services":
            push_data = {
                "template_id": "5",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", "nginx"),
                        "count": v.get("count", 3),
                        "interval": v.get("interval", 600)
                    },
                    "number_rule": {
                        "day_num": v.get("day_limit", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "panel_safe_push":
            push_data = {
                "template_id": "6",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {
                        "day_num": v.get("day_limit", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "ssh_login":
            push_data = {
                "template_id": "7",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "panel_login":
            push_data = {
                "template_id": "8",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "project_status":
            push_data = {
                "template_id": "9",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 1),
                        "project": v.get("project", 0),
                        "count": v.get("count", 2) if v.get("count", 2) not in (1, 2) else 2,
                        "interval": v.get("interval", 600)
                    },
                    "number_rule": {
                        "day_num": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "panel_update":
            push_data = {
                "template_id": "10",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {
                        "day_num": 1
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

    send_type = None
    login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"
    if os.path.exists(login_send_type_conf):
        send_type = read_file(login_send_type_conf).strip()
    else:
        # 兼容之前的
        if os.path.exists("/www/server/panel/data/login_send_type.pl"):
            send_type = read_file("/www/server/panel/data/login_send_type.pl")
        else:
            if os.path.exists('/www/server/panel/data/login_send_mail.pl'):
                send_type = "mail"
            if os.path.exists('/www/server/panel/data/login_send_dingding.pl'):
                send_type = "dingding"

    if isinstance(send_type, str):
        sender_list = [df_mdl[i.strip()] for i in send_type.split(",") if i.strip() in df_mdl]
        push_data = {
            "template_id": "8",
            "task_data": {
                "status": True,
                "sender": sender_list,
                "task_data": {},
                "number_rule": {}
            }
        }
        pmgr.set_task_conf_data(push_data)

    login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
    if os.path.exists(login_send_type_conf):
        ssh_send_type = read_file(login_send_type_conf).strip()
        if isinstance(ssh_send_type, str):
            sender_list = [df_mdl[i.strip()] for i in ssh_send_type.split(",") if i.strip() in df_mdl]
            push_data = {
                "template_id": "7",
                "task_data": {
                    "status": True,
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)
    return


def _update_system_push(old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
                        pmgr: PushManager,
                        df_mdl: Dict[str, str]):
    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        if v["type"] == "disk":
            push_data = {
                "template_id": "20",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", "/"),
                        "cycle": v.get("cycle", 2) if v.get("cycle", 2) not in (1, 2) else 2,
                        "count": v.get("count", 80),
                    },
                    "number_rule": {
                        "total": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        if v["type"] == "cpu":
            push_data = {
                "template_id": "21",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 5) if v.get("cycle", 5) not in (3, 5, 15) else 5,
                        "count": v.get("count", 80),
                    },
                    "number_rule": {
                        "total": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        if v["type"] == "load":
            push_data = {
                "template_id": "22",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 5) if v.get("cycle", 5) not in (1, 5, 15) else 5,
                        "count": v.get("count", 80),
                    },
                    "number_rule": {
                        "total": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        if v["type"] == "mem":
            push_data = {
                "template_id": "23",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 5) if v.get("cycle", 5) not in (3, 5, 15) else 5,
                        "count": v.get("count", 80),
                    },
                    "number_rule": {
                        "total": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

    return


def _update_database_push(old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
                          pmgr: PushManager,
                          df_mdl: Dict[str, str]):
    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        if v["type"] == "mysql_pwd_endtime":
            push_data = {
                "template_id": "30",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", []),
                        "cycle": v.get("cycle", 15),
                    },
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "mysql_replicate_status":
            push_data = {
                "template_id": "31",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", []),
                        "count": v.get("cycle", 15),
                        "interval": v.get("interval", 600)
                    },
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)

    return None


def _update_rsync_push(
        old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
        pmgr: PushManager,
        df_mdl: Dict[str, str]):
    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        push_data = {
            "template_id": "40",
            "task_data": {
                "status": bool(v.get("status", True)),
                "sender": sender_list,
                "task_data": {
                    "interval": v.get("interval", 600)
                },
                "number_rule": {
                    "day_num": v.get("push_count", 3)
                }
            }
        }
        pmgr.set_task_conf_data(push_data)


def _update_load_push(
        old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
        pmgr: PushManager,
        df_mdl: Dict[str, str]):
    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        push_data = {
            "template_id": "50",
            "task_data": {
                "status": bool(v.get("status", True)),
                "sender": sender_list,
                "task_data": {
                    "project": v.get("project", ""),
                    "cycle": v.get("cycle", "200|301|302|403|404")
                },
                "number_rule": {
                    "day_num": v.get("push_count", 2)
                }
            }
        }

        pmgr.set_task_conf_data(push_data)


def _update_task_manager_push(
        old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
        pmgr: PushManager,
        df_mdl: Dict[str, str]):
    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        template_id_dict = {
            "task_manager_cpu": "60",
            "task_manager_mem": "61",
            "task_manager_process": "62"
        }
        if v["type"] in template_id_dict:
            push_data = {
                "template_id": template_id_dict[v["type"]],
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", ""),
                        "count": v.get("count", 80),
                        "interval": v.get("count", 600),
                    },
                    "number_rule": {
                        "day_num": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)


def update_mod_push_system2():
    pmgr = PushManager()
    default_module_dict = get_default_module_dict()
    _update_ftp_log_push(pmgr, default_module_dict)
    _update_ftp_user_push(pmgr, default_module_dict)
    _update_web_log_push(pmgr, default_module_dict)
    _update_site_content_push(pmgr, default_module_dict)
    _update_vulnerability_scanning(pmgr, default_module_dict)
    _update_file_detect_task(pmgr, default_module_dict)


def _update_ftp_log_push(pmgr: PushManager, df_mdl: Dict[str, str]):
    old_file = "/www/server/panel/data/analysis_config.json"
    try:
        data = json.loads(read_file(old_file))
    except:
        return
    if bool(data["cron_task_status"]) and data.get("cron_task", None):
        cron_task = data["cron_task"]
        push_data = {
            "template_id": "101",
            "task_data": {
                "status": bool(data.get("cron_task_status", True)),
                "sender": [df_mdl[i.strip()] for i in cron_task.get("channel", "").split(",") if i.strip() in df_mdl],
                "task_data": {
                    "task_type": [k for k, v in cron_task.get("task_type", {}).items() if v],
                },
                "number_rule": {
                    "day_num": 1
                }
            }
        }
        pmgr.set_task_conf_data(push_data)
        if '/www/server/panel/class/' not in sys.path:
            sys.path.insert(0, '/www/server/panel/class/')
        import crontab
        import public
        name = '[勿删]FTP日志分析任务'
        cron_id = public.M('crontab').where("name=?", (name,)).getField('id')
        if cron_id:
            args = {"id": cron_id}
            crontab.crontab().DelCrontab(args)


def _update_ftp_user_push(pmgr: PushManager, df_mdl: Dict[str, str]):
    old_file = "/www/server/panel/data/ftp_push_config.json"
    try:
        data = json.loads(read_file(old_file))
    except:
        return

    if len(data.get("1", [])) + len(data.get("2", [])) + len(data.get("3", [])) > 0:
        push_data = {
            "template_id": "102",
            "task_data": {
                "status": True,
                "sender": [df_mdl[i.strip()] for i in data.get("channel", "").split(",") if i.strip() in df_mdl],
                "task_data": {},
                "number_rule": {
                    "day_num": 1
                }
            }
        }
        pmgr.set_task_conf_data(push_data)
        if '/www/server/panel/class/' not in sys.path:
            sys.path.insert(0, '/www/server/panel/class/')
        import crontab
        import public
        name = "【勿删】ftp定时检测密码有效期任务"
        cron_id = public.M('crontab').where("name=?", (name,)).getField('id')
        if cron_id:
            args = {"id": cron_id}
            crontab.crontab().DelCrontab(args)


def _update_web_log_push(pmgr: PushManager, df_mdl: Dict[str, str]):
    old_file = "/www/server/panel/data/cron_task_analysis.json"
    try:
        data: dict = json.loads(read_file(old_file))
    except:
        # debug_log(traceback.format_exc())
        return

    sender = [df_mdl[i.strip()] for i in data.get("channel", "").split(",") if i.strip() in df_mdl]
    for path in data.keys():
        if path == "channel":
            continue
        if os.path.exists(path):
            try:
                name = os.path.basename(path).rsplit(".", 1)[0]
            except:
                # debug_log(traceback.format_exc())
                continue
            push_data = {
                "template_id": "110",
                "task_data": {
                    "status": True,
                    "sender": sender,
                    "task_data": {
                        "site_name": name
                    },
                    "number_rule": {
                        "day_num": 1
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)


def _update_site_content_push(pmgr: PushManager, df_mdl: Dict[str, str]):
    db_file = "/www/server/panel/class/projectModel/content/content.db"
    if not os.path.exists(db_file):
        return
    db_obj = get_db_by_file(db_file)
    if not db_obj:
        return

    data_list = db_obj.table("monitor_site").where("send_msg = 1", ()).field("id,site_name,send_type").select()
    for data in data_list:
        sender = []
        for i in data.get("send_type", "").split(","):
            if i.strip() in df_mdl:
                sender.append(df_mdl[i.strip()])
            if len(i) == 16:
                sender.append(i)

        push_data = {
            "template_id": "121",
            "task_data": {
                "status": True,
                "sender": sender,
                "task_data": {
                    "site_name": data.get("site_name", ""),
                    "mvw_id": data["id"],
                }
            }
        }
        r = pmgr.set_task_conf_data(push_data)


def _update_vulnerability_scanning(pmgr: PushManager, df_mdl: Dict[str, str]):
    if '/www/server/panel/class/' not in sys.path:
        sys.path.insert(0, '/www/server/panel/class/')
    name = "[勿删]漏洞扫描定时任务"
    cron_data = DB('crontab').where("name=?", (name,)).field('id,sBody,where1').find()
    if cron_data:
        sender_str_list = cron_data["sBody"].rsplit(" ", 1)
        if len(sender_str_list) == 2:
            sender_str = sender_str_list[1]
        else:
            sender_str = ""

        sender = []
        for i in sender_str.split(","):
            if i.strip() in df_mdl:
                sender.append(df_mdl[i.strip()])
            if len(i) == 16:
                sender.append(i)

        push_data = {
            "template_id": "122",
            "task_data": {
                "status": True,
                "sender": sender,
                "task_data": {
                    "cycle": int(cron_data["where1"])
                },
                "number_rule": {
                    "day_num": 1
                }
            }
        }
        aaa = pmgr.set_task_conf_data(push_data)


def _update_file_detect_task(pmgr: PushManager, df_mdl: Dict[str, str]):
    if '/www/server/panel/class/' not in sys.path:
        sys.path.insert(0, '/www/server/panel/class/')
    name = "[勿删]文件完整性监控定时任务"
    cron_data = DB('crontab').where("name=?", (name,)).field('id,sBody,hour,minute').find()
    if cron_data:
        sender_str_list = cron_data["sBody"].rsplit(" ", 1)
        if len(sender_str_list) == 2:
            sender_str = sender_str_list[1]
        else:
            sender_str = ""

        sender = []
        for i in sender_str.split(","):
            if i.strip() in df_mdl:
                sender.append(df_mdl[i.strip()])
            if len(i) == 16:
                sender.append(i)

        push_data = {
            "template_id": "123",
            "task_data": {
                "status": True,
                "sender": sender,
                "task_data": {
                    "hour": int(cron_data["hour"]),
                    "minute": int(cron_data["minute"])
                },
                "number_rule": {
                    "day_num": 1
                }
            }
        }
        aaa = pmgr.set_task_conf_data(push_data)
        # debug_log(aaa)
