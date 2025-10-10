
#coding: utf-8
import os,sys
sys.path.insert(0,"/www/server/panel/class/")
try:
    import send_to_user
    msg=send_to_user.send_to_user()
    msg.main()
except:
    pass