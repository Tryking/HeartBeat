#!/usr/bin/python
# -*- coding: utf-8 -*-
import pymongo
from lib.common import *

file_abs = "C:\\Users\\Tryking\\Desktop\\monitor_task.txt"

client = pymongo.MongoClient(MONGO_URL, int(MONGO_PORT), connect=False)
mongodb = client[MONGO_DB]
mongodb.authenticate(MONGO_USERNAME, MONGO_PWD)
table_task = MONGO_TABLE_TASK

result = []
column_name = ["id", "name", "url", "source", "instance", "scheme", "method", "params", "response_match_enable",
               "response_match", "req_count", "cost_risk_max", "cost_risk_average", "iface_protocol", "enable",
               "add_time", "update_time", "last_check_time", "send__users", "intval_time"]

try:
    with open(file_abs, "r") as f:
        for line in f:
            split = str.split(line, "\t")
            result.append(split)
finally:
    if f:
        f.close()

for i in result:
    temp = {column_name[0]: int(i[0][1:-1]),
            column_name[1]: str(i[1][1:-1]),
            column_name[2]: str(i[2][1:-1]),
            column_name[3]: int(i[3][1:-1]),
            column_name[4]: str(i[4][1:-1]),
            column_name[5]: str(i[5][1:-1]),
            column_name[6]: str(i[6][1:-1]),
            column_name[7]: str(i[7][1:-1]),
            column_name[8]: int(i[8][1:-1]),
            column_name[9]: str(i[9][1:-1]),
            column_name[10]: int(i[10][1:-1]),
            column_name[11]: int(i[11][1:-1]),
            column_name[12]: int(i[12][1:-1]),
            column_name[13]: int(i[13][1:-1]),
            column_name[14]: int(i[14][1:-1]),
            column_name[15]: timeToFormat(formatToTime(str(i[15][1:-1]).replace("/", "-"))),
            column_name[16]: timeToFormat(formatToTime(i[16][1:-1].replace("/", "-"))),
            column_name[17]: timeToFormat(formatToTime(i[17][1:-1].replace("/", "-"))),
            column_name[18]: str(i[18][1:-1]),
            column_name[19]: int(i[19][1:-2])
            }
    mongodb[table_task].insert_one(temp)
