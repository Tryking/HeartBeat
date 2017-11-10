#!/usr/bin/env python
# -*-encoding:UTF-8-*-
import ConfigParser
import re
import logging
import logging.handlers
import sys
import os
import subprocess
import threading
import socket
import struct
import urllib
import urllib2
import httplib
import httplib2
import inspect
import time
import random
import datetime
from Queue import Queue

CONFIG = "./lib/common.conf"
cfg = ConfigParser.RawConfigParser()
cfg.readfp(open(CONFIG))

# 获取配置
MONGO_URL = cfg.get("mongo", "mongo_url").replace('"', '')
MONGO_PORT = cfg.get("mongo", "mongo_port").replace('"', '')
MONGO_DB = cfg.get("mongo", "mongo_db").replace('"', '')
MONGO_TABLE_RESULT = cfg.get("mongo", "mongo_table_result").replace('"', '')
MONGO_TABLE_TASK = cfg.get("mongo", "mongo_table_task").replace('"', '')
MONGO_USERNAME = cfg.get("mongo", "mongo_username").replace('"', '')
MONGO_PWD = cfg.get("mongo", "mongo_pwd").replace('"', '')


def initLog(console_level, file_level, logfile):
    formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s')
    logging.getLogger().setLevel(0)
    console_log = logging.StreamHandler()
    console_log.setLevel(console_level)
    console_log.setFormatter(formatter)
    file_log = logging.handlers.RotatingFileHandler(logfile, maxBytes=1024 * 1024, backupCount=2)
    file_log.setLevel(file_level)
    file_log.setFormatter(formatter)
    logging.getLogger().addHandler(file_log)
    logging.getLogger().addHandler(console_log)


def writeFileLog(msg, module='', level='error'):
    filename = os.path.split(__file__)[1]
    if level == 'debug':
        logging.getLogger().debug('File:' + filename + ', ' + module + ': ' + msg)
    elif level == 'warning':
        logging.getLogger().warning('File:' + filename + ', ' + module + ': ' + msg)
    else:
        logging.getLogger().error('File:' + filename + ', ' + module + ': ' + msg)


def DEBUG(msg):
    module = ""
    writeFileLog(msg, module, 'debug')


def ERROR(msg):
    module = ""
    writeFileLog(msg, module, 'error')


def popen(cmd):
    try:
        return subprocess.Popen(cmd, shell=True, close_fds=True, bufsize=-1, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).stdout.readlines()
    except Exception, e:
        print str(e)
        return ''


def getCurrentFunctionName():
    return inspect.stack()[1][3]


def toStr(msg):
    try:
        return msg.encode('utf-8')
    except Exception, e:
        return ''


def httpRequest(url, method, headers, body, timeout, enable_forward):
    http = httplib2.Http()
    if enable_forward:
        http.follow_redirects = True
    else:
        http.follow_redirects = False
    socket.setdefaulttimeout(timeout)
    response, content = http.request(url, method, headers=headers, body=body)
    return response, content


def checkProcessExist(process):
    try:
        result = popen("ps -ef | grep %s | grep -v grep | wc -l" % process)
        if result and int(result[0]) > 0:
            return True
        return False
    except Exception, e:
        return False


class Util:
    socketLocker = threading.Lock()
    flowLocker = threading.Lock()

    @classmethod
    def addTimeout(cls, t=5):
        cls.socketLocker.acquire()
        timeout = socket.getdefaulttimeout()
        if timeout:
            if timeout < 115:
                socket.setdefaulttimeout(timeout + t)
        cls.socketLocker.release()

    @classmethod
    def subTimeout(cls, t=5):
        cls.socketLocker.acquire()
        timeout = socket.getdefaulttimeout()
        if timeout:
            if timeout > 10:
                socket.setdefaulttimeout(timeout - t)
        cls.socketLocker.release()


def checkIpv4(ip):
    match = re.findall(
        u"^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$",
        ip, re.I)
    if match and len(match) > 0:
        return True
    else:
        return False


def checkIpv4Inner(ip):
    match = re.findall(
        u"(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])",
        ip, re.I)
    if match and len(match) > 0:
        return True
    else:
        return False


def checkIpv4Range(ip_range):
    match = re.findall(
        u"^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])-(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$",
        ip_range, re.I)
    if match and len(match) > 0:
        return True
    else:
        return False
        # end if


# end def

def checkIpv6(ipv6_addr):
    try:
        addr = socket.inet_pton(socket.AF_INET6, ipv6_addr)
    except socket.error:
        return False
    else:
        return True


def checkIpv6Inner(ipaddr):
    ip = ipaddr.upper()
    match = re.findall(
        u"((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?",
        ip, re.I)
    if match and len(match) > 0:
        return True
    else:
        return False


def checkIpv6Domain(domain):
    ip = domain.upper()
    match = re.findall(
        u"^\[((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\]$",
        ip, re.I)
    if match and len(match) > 0:
        return True
    else:
        return False


def checkIpv6Range(ip_range):
    try:
        last_colon_index = 0
        tmp = ip_range.split('-')
        if len(tmp) == 2:
            if checkIpv6(tmp[0]):
                if checkIpv6(tmp[1]):
                    return True
                for i in range(len(tmp[0])):
                    if tmp[0][i] == ':':
                        last_colon_index = i
                tmp_line = tmp[0][last_colon_index + 1:]
                if len(tmp_line) > len(tmp[1]):
                    return False
                elif len(tmp_line) < len(tmp[1]):
                    return True
                else:
                    if cmp(tmp_line, tmp[1]) <= 0:
                        return True
                    else:
                        return False
            else:
                return False
        else:
            return False
    except Exception, e:
        return False


# 十六进制 to 十进制
def hex2dec(string_num):
    return int(string_num.upper(), 16)


# 十进制 to 十六进制
def dec2hex(string_num):
    base = [str(x) for x in range(10)] + [chr(x) for x in range(ord('A'), ord('A') + 6)]
    num = int(string_num)
    mid = []
    while True:
        if num == 0: break
        num, rem = divmod(num, 16)
        mid.append(base[rem])

    return ''.join([str(x) for x in mid[::-1]])


def ipv4Toint(addr):
    try:
        return struct.unpack("!I", socket.inet_aton(addr))[0]
    except Exception, e:
        return ''


def intToipv4(i):
    try:
        return socket.inet_ntoa(struct.pack("!I", i))
    except Exception, e:
        return ''


def fullIpv6(ip):
    if ip == "" or len(ip) < 4 or len(ip) > 39:
        return False
    # end if
    ip = ip.upper()
    match = re.findall(
        u"^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?$",
        ip, re.I)
    if match and len(match) > 0:
        ip_sep = ip.split(":")
        if len(ip_sep) < 8:
            t = 8 - len(ip_sep)
            ip = ip.replace("::", ":" * (t + 2))
        # end if
        ip_sep = ip.split(":")
        ip = []
        for row in ip_sep:
            row = "0000%s" % (row)
            ip.append(row[-4:])
        # end for
        ip = ":".join(ip)

        return ip
    else:
        return False


def easyIpv6(ip):
    if ip == "" or len(ip) < 4 or len(ip) > 39:
        return False
    # end if
    ip = ip.lower()
    match = re.findall(
        u"^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?$",
        ip, re.I)
    if match and len(match) > 0:
        ip_sep = ip.split(":")
        ip = []
        for row in ip_sep:
            i = 0
            for i in range(len(row)):
                if row == "":
                    break
                elif row == "0":
                    row = "0"
                    break
                elif row[0] == "0":
                    row = row[1:]
                else:
                    break

            ip.append(row)

        if len(ip) == 8:
            ip = ":".join(ip)
            i = 8
            while i > 1:
                index = ip.find(":" + "0:" * i)
                if index > 0:
                    ip = "%s::%s" % (ip[0:index], ip[index + (2 * i + 1):])
                    break

                i -= 1

        else:
            ip = ":".join(ip)

        return ip
    else:
        return False


def getIpv4Range(ip_start, ip_end):
    ip_list = []
    ip_start_int = ipv4Toint(ip_start)
    ip_end_int = ipv4Toint(ip_end)

    if ip_start_int > ip_end_int:
        ip_list = False
    elif ip_start_int == ip_end_int:
        ip_list.append(ip_start)
    else:
        for i in range(ip_start_int, ip_end_int + 1):
            ip = intToipv4(i)
            ip_list.append(ip)

    return ip_list


def getIpv6Range(ip_start, ip_end):
    ip_list = []
    ip_start = fullIpv6(ip_start)
    ip_end = fullIpv6(ip_end)

    if ip_start == False or ip_end == False:
        return False
    if ip_start == ip_end:
        ip_list.append(easyIpv6(ip_start))
        return ip_list
    if cmp(ip_start, ip_end) == 1:
        return False

    ip_org = ""
    i = 0
    for i in range(len(ip_start)):
        if ip_start[i] != ip_end[i]:
            ip_org = ip_start[0:i]
            ip_start = ip_start[i:]
            ip_end = ip_end[i:]
            break

    if len(ip_start) > 4:
        return False
    j = len(ip_start)

    for i in range(hex2dec(ip_start), hex2dec(ip_end) + 1):
        t = dec2hex(i)
        t = "0000%s" % (t)
        t = "%s%s" % (ip_org, t[-j:])
        ip_list.append(easyIpv6(t))

    return ip_list


def domainToip(domain):
    try:
        if domain == "":
            return False
        if domain.find("://") > 0:
            domain = domain.split("://")[1]
        if checkIpv4(domain) or checkIpv6(domain):
            return domain
        match = re.findall(
            u"((\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5]))",
            domain, re.I)
        if match and len(match) > 0:
            print match
            return match[0][0]

        match = re.findall(
            u"((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?",
            domain, re.I)
        if match and len(match) > 0:
            return match[0][0]
        if domain.find(":") > 0:
            if len(domain.split(":") > 2):
                return False
            else:
                domain = domain.split(":")[0]

        res = socket.getaddrinfo(domain, None)
        if res and len(res) > 0:
            return res[0][4][0]

        return False

    except Exception, e:
        return False


def ipv6ToBin(ipv6):
    try:
        tmp = fullIpv6(ipv6)
        if tmp == False:
            return False
        res_ip = ''
        ret = []
        for i in range(len(tmp)):
            if tmp[i] != ':':
                res = bin(int(tmp[i], 16))
                res = res[2:]
                a = len(res)
                if a < 4:
                    r = ''
                    for j in range(4 - a):
                        r += '0'
                    res += r
                res_ip += res

        return res_ip

    except Exception, e:
        return False


def getCurrentTimestamp():
    return time.time()


def getCurrentTimeFormat():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def timeToFormat(timestamp):
    try:
        timeFormat = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        return timeFormat
    except Exception, e:
        raise e


def formatToTime(timeFormat):
    try:
        timeArray = time.strptime(timeFormat, "%Y-%m-%d %H:%M:%S")
        timestamp = time.mktime(timeArray)

        return timestamp
    except Exception, e:
        raise e


def getMicrosecond():
    formatTime = str(datetime.datetime.now())
    timestamp = formatToTime(formatTime.split('.')[0]) * 1000 + float(formatTime.split('.')[1][0:3])

    return timestamp


def getRandomStr(strlen):
    content = 'abcdefghijklmnopqrstuvwxyz1234567890'
    minIndex = 0
    maxIndex = len(content) - 1
    output = []
    for i in range(strlen):
        index = random.randint(minIndex, maxIndex)
        output.append(content[index:index + 1])
    output = "".join(output)

    return output


def getRandomNumberStr(strlen):
    content = '123456789'
    minIndex = 0
    maxIndex = len(content) - 1
    output = []
    for i in range(strlen):
        index = random.randint(minIndex, maxIndex)
        output.append(content[index:index + 1])
    output = "".join(output)

    return output
