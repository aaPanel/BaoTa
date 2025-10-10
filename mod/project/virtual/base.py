# coding: utf-8
import os, sys, time, json

panelPath = '/www/server/panel'
os.chdir(panelPath)
if not panelPath + "/class/" in sys.path:
    sys.path.insert(0, panelPath + "/class/")
import public, re


class virtualBase:

    def __init__(self):
        pass