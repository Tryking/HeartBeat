#!/usr/bin/python
# -*- coding: utf-8 -*-

from lib.common import *

s = "2017/11/7 12:01:17"
s = s.replace("/", "-")
time = formatToTime(s)
time = timeToFormat(time)
print time