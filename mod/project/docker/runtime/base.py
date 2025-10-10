# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型 - docker runtime 基类
# ------------------------------
import json
import os
import sys
import time
from datetime import datetime, timedelta

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from mod.project.docker.composeMod import main as composeMod


class Runtime(composeMod):

    def __init__(self):
        super(Runtime, self).__init__()