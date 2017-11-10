#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import urlparse
import pymongo
import simplejson as simplejson

from lib.common import *
from lib.HttpRequest import *

client = pymongo.MongoClient(MONGO_URL, int(MONGO_PORT), connect=False)
mongodb = client[MONGO_DB]
mongodb.authenticate(MONGO_USERNAME, MONGO_PWD)
table_result = MONGO_TABLE_RESULT
table_task = MONGO_TABLE_TASK


class IfaceMonitorProducer(threading.Thread):
    def __init__(self, threadName, queue, threadLock):
        try:
            threading.Thread.__init__(self)
            self.module = self.__class__.__name__
            self.threadName = threadName
            self.queue = queue
            self.threadLock = threadLock
            self.http = HttpRequest({'timeout': 120})
            socket.setdefaulttimeout(120)
        except Exception, e:
            writeFileLog(str(e), getCurrentFunctionName())

    def writeFileLog(self, msg, module='', level='error'):
        filename = os.path.split(__file__)[1]
        if level == 'debug':
            logging.getLogger().debug('File:' + filename + ', ' + module + ': ' + msg)
        elif level == 'warning':
            logging.getLogger().warning('File:' + filename + ', ' + module + ': ' + msg)
        else:
            logging.getLogger().error('File:' + filename + ', ' + module + ': ' + msg)

    # 调试日志
    def debug(self, msg, funcName=''):
        module = "%s.%s" % (self.module, funcName)
        msg = "threadName: %s, %s" % (self.threadName, msg)
        self.writeFileLog(msg, module, 'debug')

    # 错误日志
    def error(self, msg, funcName=''):
        module = "%s.%s" % (self.module, funcName)
        msg = "threadName: %s, %s" % (self.threadName, msg)
        self.writeFileLog(msg, module, 'error')

    def getMonitorList(self):
        try:
            cursor = mongodb[table_task].find({"enable": 1})
            for v in cursor:
                print v['id']
                lastCheckTime = v['last_check_time']
                if lastCheckTime is None:
                    lastCheckTime = ''
                else:
                    lastCheckTime = v['last_check_time']
                if lastCheckTime is None or lastCheckTime == '0000-00-00 00:00:00' or lastCheckTime == '':
                    lastCheckTimestamp = 0
                else:
                    lastCheckTimestamp = formatToTime(lastCheckTime)
                intvalTime = int(v['intval_time'])
                currentTimestamp = time.time()
                if currentTimestamp > lastCheckTimestamp + intvalTime:
                    self.queue.put(v)
            return True
        except Exception, e:
            self.error(str(e), getCurrentFunctionName())
            return False

        except Exception, e:
            self.error(str(e), getCurrentFunctionName())
            return False

    def run(self):
        try:
            while True:
                try:
                    self.getMonitorList()
                except Exception, e2:
                    self.error(str(e2), getCurrentFunctionName())
                time.sleep(10)
        except Exception, e:
            self.error(str(e), getCurrentFunctionName())


class IfaceMonitorConsumer(threading.Thread):
    def __init__(self, threadName, queue, threadLock):
        try:
            threading.Thread.__init__(self)
            self.module = self.__class__.__name__
            self.threadName = threadName
            self.queue = queue
            self.threadLock = threadLock
            self.http = HttpRequest({'timeout': 120})
            socket.setdefaulttimeout(120)
        except Exception, e:
            writeFileLog(str(e), getCurrentFunctionName())

    def writeFileLog(self, msg, module='', level='error'):
        filename = os.path.split(__file__)[1]
        if level == 'debug':
            logging.getLogger().debug('File:' + filename + ', ' + module + ': ' + msg)
        elif level == 'warning':
            logging.getLogger().warning('File:' + filename + ', ' + module + ': ' + msg)
        else:
            logging.getLogger().error('File:' + filename + ', ' + module + ': ' + msg)

    # 调试日志
    def debug(self, msg, funcName=''):
        module = "%s.%s" % (self.module, funcName)
        msg = "threadName: %s, %s" % (self.threadName, msg)
        self.writeFileLog(msg, module, 'debug')

    # 错误日志
    def error(self, msg, funcName=''):
        module = "%s.%s" % (self.module, funcName)
        msg = "threadName: %s, %s" % (self.threadName, msg)
        self.writeFileLog(msg, module, 'error')

    def requestUrl(self, ifaceProtocol, url, method, params, reqCount, responseMatchEnable, responseMatch):
        parse = urlparse.urlparse(url)
        scheme = parse[0]
        instance = parse[1]
        response = {'url': url, 'instance': instance, 'reqCount': reqCount, 'costMin': 0, 'costMax': 0,
                    'costAverage': 0, 'reqSuccess': 0, 'reqError': 0}
        try:
            if params == '':
                params = {}
            else:
                params = simplejson.loads(params)

            reqList = []
            for i in range(reqCount):
                try:
                    start = getMicrosecond()
                    res, content = self.http.request(url, method, params)
                    cost = int(getMicrosecond() - start)
                    status = res['status']

                    reqList.append({'status': status, 'cost': cost, 'content': content})
                except Exception, e1:
                    self.error("http.request error:" + str(e1), getCurrentFunctionName())

            costTotal = 0
            for v in reqList:
                status = v['status']
                cost = v['cost']
                costTotal += cost
                if status == '200' and (responseMatchEnable == 0 or (responseMatch == '' and v['content'] == '') or (
                                responseMatch != '' and v['content'].find(responseMatch) >= 0)):
                    response['reqSuccess'] += 1
                if response['costMin'] == 0 or cost < response['costMin']:
                    response['costMin'] = cost
                if response['costMax'] == 0 or cost > response['costMax']:
                    response['costMax'] = cost

            if len(reqList) > 0 and costTotal > 0:
                response['costAverage'] = int(costTotal / len(reqList))

            response['reqError'] = response['reqCount'] - response['reqSuccess']
            return response
        except Exception, e:
            self.error(str(e), getCurrentFunctionName())
            return response

    def updateInstanceData(self, taskId, name, reqNo, source, data):
        try:
            params = {
                'task_id': taskId,
                'name': name,
                'req_no': reqNo,
                'source': source,
                'url': data['url'],
                'instance': data['instance'],
                'req_count': data['reqCount'],
                'cost_min': data['costMin'],
                'cost_max': data['costMax'],
                'cost_average': data['costAverage'],
                'req_time': getCurrentTimeFormat(),
                'req_success_count': data['reqSuccess'],
                'req_error_count': data['reqError']
            }
            mongodb[table_result].insert_one(params)

            if params['req_error_count'] != 0:
                self.debug("name: %s,url: %s,instance: %s,source: %s was fail, the fail times is [%s/%s]" % (
                    str(params['name']), str(params['url']), str(params['instance']), str(params['source']),
                    str(params['req_error_count']), str(params['req_count'])))

            return True
        except Exception, e:
            self.error(str(e), getCurrentFunctionName())
            return False

    def updateTaskData(self, taskId):
        try:
            mongodb[table_task].update_one({"id": taskId}, {'$set': {"last_check_time": getCurrentTimeFormat()}},
                                           upsert=False)
            return True
        except Exception, e:
            self.error(str(e), getCurrentFunctionName())
            return False

    def checkTask(self, taskInfo):
        try:
            reqNo = getRandomStr(32)
            url = taskInfo['url']
            name = taskInfo['name'].encode('utf8')
            source = int(taskInfo['source'])
            instance = taskInfo['instance']
            if instance != '':
                instance = instance.encode('utf8')
            scheme = taskInfo['scheme']
            if scheme != '':
                scheme = scheme.encode('utf8')
            method = taskInfo['method']
            if method != '':
                method = method.encode('utf8')
            params = taskInfo['params']
            if params != '':
                params = params.encode('utf8')
            reqCount = taskInfo['req_count']
            ifaceProtocol = taskInfo['iface_protocol']
            responseMatch = taskInfo['response_match']
            if responseMatch != '':
                responseMatch = responseMatch.encode('utf8')
            # end if
            responseMatchEnable = int(taskInfo['response_match_enable'])

            i = 0
            if url.find("https://") >= 0 or url.find("http://") >= 0:
                i += 1
                response = self.requestUrl(ifaceProtocol, url, method, params, reqCount, responseMatchEnable,
                                           responseMatch)
                self.updateInstanceData(taskInfo['id'], "%s-%d" % (name, i), reqNo, source, response)
            else:
                instanceList = instance.split(",")
                for instance in instanceList:
                    i += 1
                    realUrl = "%s://%s%s" % (scheme, instance, url)
                    response = self.requestUrl(ifaceProtocol, realUrl, method, params, reqCount, responseMatchEnable,
                                               responseMatch)
                    self.updateInstanceData(taskInfo['id'], "%s-%d" % (name, i), reqNo, source, response)

            self.updateTaskData(taskInfo['id'])

            return True
        except Exception, e:
            self.error(str(e), getCurrentFunctionName())
            return False

    def run(self):
        try:
            while True:
                try:
                    # 从队列里面获取数据
                    record = None
                    try:
                        record = self.queue.get(True, 30)
                    except Exception, ge:
                        pass

                    if record is None or len(record) == 0:
                        continue

                    self.checkTask(record)

                except Exception, e2:
                    self.error(str(e2), getCurrentFunctionName())
        except Exception, e:
            self.error(str(e), getCurrentFunctionName())


class IfaceMonitor():
    def __init__(self):
        try:
            self.module = self.__class__.__name__
            self.http = HttpRequest({'timeout': 120})
            socket.setdefaulttimeout(120)
        except Exception, e:
            writeFileLog(str(e), getCurrentFunctionName())

    def writeFileLog(self, msg, module='', level='error'):
        filename = os.path.split(__file__)[1]
        if level == 'debug':
            logging.getLogger().debug('File:' + filename + ', ' + module + ': ' + msg)
        elif level == 'warning':
            logging.getLogger().warning('File:' + filename + ', ' + module + ': ' + msg)
        else:
            logging.getLogger().error('File:' + filename + ', ' + module + ': ' + msg)

    # 调试日志
    def debug(self, msg, funcName=''):
        module = "%s.%s" % (self.module, funcName)
        self.writeFileLog(msg, module, 'debug')

    # 错误日志
    def error(self, msg, funcName=''):
        module = "%s.%s" % (self.module, funcName)
        self.writeFileLog(msg, module, 'error')

    def main(self, threadNum):
        try:
            queue = Queue()
            threadLock = threading.Lock()
            threadList = []
            producer = IfaceMonitorProducer('producer', queue, threadLock)
            threadList.append(producer)

            for i in range(threadNum):
                threadName = "thread-%d" % (i)

                t = IfaceMonitorConsumer(threadName, queue, threadLock)
                threadList.append(t)

            for t in threadList:
                t.start()

            for t in threadList:
                t.join()

            return True
        except Exception, e:
            self.writeFileLog(str(e), getCurrentFunctionName())
            return False


if __name__ == '__main__':
    initLog(logging.DEBUG, logging.DEBUG, "logs/" + os.path.split(__file__)[1].split(".")[0] + ".log")

    writeFileLog('The application run start at: %s' % str(getCurrentTimeFormat()))

    ifaceMonitor = IfaceMonitor()
    ifaceMonitor.main(100)
