#!/www/server/panel/pyenv/bin/python
#coding: utf-8
import os,sys
os.chdir("/www/server/panel")
sys.path.insert(0,"class/")
from projectModel.quotaModel import main
p = main()
p.mysql_quota_check()
