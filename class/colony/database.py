#!/usr/bin/python
# coding: utf-8
"""

author: linxiao
date: 2021/1/23 9:45
"""
from colony import mysql


class DatabaseNode:

    host = "localhost"
    user = None
    authentication_string = None
    port = 3306

    def connect(self):
        pass
