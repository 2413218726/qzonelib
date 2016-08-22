"""
MIT LICENSE
"""

import json

from qqlib import qzone


class ModeNotFoundError(Exception):
    pass


class QQManager(object):
    def __init__(self, conf_):
        self.conf = conf_
        self.qqSet = set()
        self.usedQQSet = set()
        self.loadQQFromConf()

    def loadQQFromConf(self):
        conf_ = open(self.conf)
        for line in conf_.readlines():
            [qq_, pwd] = line.split(":")
            qq_ = str(qq_).lstrip().rstrip()
            pwd = str(pwd).lstrip().rstrip()
            self.qqSet.add((qq_, pwd))

    def hasQQ(self):
        return len(self.qqSet) != 0

    def nextQQ(self):
        qq_ = None
        if self.hasQQ():
            qq_ = self.qqSet.pop()
            self.usedQQSet.add(qq_)
        print('已取得下一个qq信息： qq：%s, pwd:%s' % (qq_[0], qq_[1]))
        return qq_


ALL = 0  # 爬取提供qq的所有说说，默认
KEYWORD = 1  # 根据提供的关键字来点赞，仅点赞最近一条
KEYWORD_ALL = 2  # 为包含该关键字的所有说说点赞
LATEST = 3  # 为最近的一条说说点赞


class QzoneLiker(object):
    def __init__(self, qqsearch, mode=ALL):
        self.qqSearch = qqsearch
        self.qqClient = None
        self.keyword = None
        self.qqLogin = None
        self.limit = -1
        self.mode = mode

    def __likeALL(self, tids):
        for tid in tids:
            self.__like(tid)

    def __like(self, tid):
        """
        点赞说说
        :param tid:
        :return:
        """
        url = 'http://h5.qzone.qq.com/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_dolike_app'
        resp = self.qqClient.fetch(url, params={
            'g_tk': self.qqClient.g_tk()
        }, data={
            'qzreferrer': 'http://user.qzone.qq.com/%s/taotao' % self.qqSearch,
            'opuin': '%s' % self.qqSearch,
            'unikey': 'http://user.qzone.qq.com/%s/mood/%s' % (self.qqSearch, tid),
            'curkey': 'http://user.qzone.qq.com/%s/mood/%s' % (self.qqSearch, tid),
            'from': '-100',
            'fupdate': '1',
            'face': '0',
        })
        if resp.status_code == 200:
            print('qq:%s 已为 qq：%s 的说说:%s 点赞成功' % (self.qqLogin, self.qqSearch, tid))
            return resp

    def __loadShuoJson(self, pos, num):
        """
        加载json
        :param self:
        :param pos:
        :param num:
        :return:
        """
        shuoshuourl = 'https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6?'
        data = {
            'uin': self.qqSearch,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'hostUin': self.qqSearch,
            'notice': '0',
            'sort': '0',
            'pos': pos,
            'num': num,
            'cgi_host': 'http://taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6',
            'code_version': '1',
            'format': 'jsonp',
            'need_private_comment': 1,
            'g_tk': self.qqClient.g_tk()
        }
        return self.qqClient.fetch(url=shuoshuourl, data=None, params=data)

    def __getMsgList(self, pos, num):
        """
        通过调用 r = self.__loadShuoJson(pos=pos, num=num) 来获取伪json，
        如果响应码为200 则解析json，返回 msglist

        :param pos:
        :param num:
        :return: msglist
        """
        r = self.__loadShuoJson(pos=pos, num=num)

        if r.status_code == 200:
            jsonStr = r.text.replace('_Callback(', '')
            jsonStr = jsonStr.replace(');', '')

            jsonObj = json.loads(jsonStr)
            try:
                msglist = jsonObj['msglist']
            except KeyError:
                print(jsonObj['message'])
                return None
            return msglist

    def __getTids(self, pos, num):
        msglist = self.__getMsgList(pos, num)
        tids = list()
        for msg in msglist:
            tids.append(msg['tid'])
        return tids

    def __getTidsAll(self):
        """
        通过调用 self.__getMsgList(pos, num) 来获取msglist
        :return:
        """
        pos = 0
        num = 20
        tids = list()
        isKeywordAll = self.mode == KEYWORD_ALL
        last = False
        while True:
            if last:
                break
            if self.limit != -1:  # 是否设置了Limit
                if pos < self.limit < pos + num:
                    num = self.limit - pos
                    last = True

            msglist = self.__getMsgList(pos, num)
            if msglist is None:
                break
            for msg in msglist:
                if isKeywordAll:
                    if self.keyword not in msg['content']:
                        continue
                tids.append(msg['tid'])
            pos += num
        return tids

    def __getTidByKeyword(self):
        pos = 0
        num = 20

        found = False
        isKeyword = self.mode == KEYWORD
        if not isKeyword:
            return None

        while not found:
            msglist = self.__getMsgList(pos, num)
            if msglist is None:
                break
            for msg in msglist:
                if self.keyword in msg['content']:
                    self.tid = msg['tid']
                    print('已取得bc包含关键字“%s”说说id...%s' % (self.keyword, self.tid))
                    return self.tid
        pos += num

    def setLimit(self, limit):
        self.limit = limit
        return self

    def setKeyWord(self, keyword_):
        self.keyword = keyword_
        return self

    def login(self, qq_, pwd):
        """
        使用qqlib来登陆空间，使用该缓存点赞说说
        :param qq_:
        :param pwd:
        :return:
        """
        self.qqClient = qzone.QZone(qq_, pwd)
        self.qqClient.login()
        self.qqLogin = qq_
        print('%s 登陆成功' % qq_)
        return self

    def like(self):
        """
        供用户调用api
        为之前所设置的符合条件的说说点赞
        :return:
        """
        if self.mode == KEYWORD or self.mode == KEYWORD_ALL:
            if self.keyword is None:
                print("请使用setKeyword()来设置关键字")
                return None

        if self.mode == KEYWORD:
            tid = self.__getTidByKeyword()
            if tid is not None:
                self.__like(tid)
        elif self.mode == ALL or self.mode == KEYWORD_ALL:
            tids = self.__getTidsAll()
            self.__likeALL(tids)
        elif self.mode == LATEST:
            tid = self.__getTids(0, 1)[0]
            self.__like(tid)
        else:
            ModeNotFoundError()

    def likeBatch(self, configFile):
        qqManager = QQManager(configFile)  # 耦合
        while qqManager.hasQQ():
            xqq_, xpwd_ = qqManager.nextQQ()
            self.login(xqq_, xpwd_)
            self.like()


if __name__ == '__main__':
    conf = 'qqlist.ini'  # qq号配置文件，多qq批量点赞

    qq = '10001'  # 被点赞的qq号
    keyword = 'keyword'  # 说说关键字，ALL模式下无需指定

    liker = QzoneLiker(qq, mode=ALL)  # 此模式为默认模式，无需设置keyword
    liker = QzoneLiker(qq, mode=LATEST)  # 为最近的一条说说点赞
    liker = QzoneLiker(qq, mode=KEYWORD).setKeyWord(keyword)  # 必须设置keyword
    liker = QzoneLiker(qq, mode=KEYWORD_ALL).setKeyWord(keyword)  # 必须设置keyword

    # 单独登陆指定qq
    liker.login('10000', 'password')
    liker.like()
    # 可以批量处理指定配置文件中的qq号信息
    liker.likeBatch(conf)
