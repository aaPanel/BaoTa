#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# sqlite模型
#------------------------------
import os,sys,re,json,shutil,psutil,time
from databaseModel.base import databaseBase
import public


class main(databaseBase):

    def get_list(self,args):

        return []