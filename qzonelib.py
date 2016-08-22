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
            [qq, pwd] = line.split(":")
            qq = str(qq).lstrip().rstrip()
            pwd = str(pwd).lstrip().rstrip()
            self.qqSet.add((qq, pwd))

    def hasQQ(self):
        return len(self.qqSet) != 0

    def nextQQ(self):
        qq = None
        if self.hasQQ():
            qq = self.qqSet.pop()
            self.usedQQSet.add(qq)
        print('已取得下一个qq信息： qq：%s, pwd:%s' % (qq[0], qq[1]))
        return qq


ALL = 0  # 爬取提供qq的所有说说，默认
KEYWORD = 1  # 根据提供的关键字来
KEYWORD_ALL = 2  # 暂未设计该模式


class QzoneLiker(object):
    def __init__(self, qqsearch, mode=ALL):
        self.qqSearch = qqsearch
        self.qqClient = None
        self.keyword = None
        self.qqLogin = None
        self.tid = None
        self.mode = mode

    def __likeALL(self, tids):
        for tid in tids:
            self.__like(tid)

    def __like(self, tid):
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

        :param self:
        :param qq:
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

    def __getTidsAll(self):
        pos = 0
        num = 20
        tids = list()
        while True:
            msglist = self.__getMsgList(pos, num)
            if msglist is None:
                break
            for msg in msglist:
                tids.append(msg['tid'])
            pos += num
        return tids

    def __getTidByKeyword(self):
        pos = 0
        num = 20

        while not self.tid:  # tid为None
            msglist = self.__getMsgList(pos, num)
            if msglist is None:
                break
            for msg in msglist:
                if self.keyword in msg['content']:
                    self.tid = msg['tid']
                    print('已取得bc包含关键字“%s”说说id...%s' % (self.keyword, self.tid))
                    return self.tid
                    # print(msg['content'])
                    # print(msg['tid'])
            pos += num

    def setKeyWord(self, keyword):
        self.keyword = keyword
        return self

    def login(self, qq_, pwd):
        self.qqClient = qzone.QZone(qq_, pwd)
        self.qqClient.login()
        self.qqLogin = qq_
        print('%s 登陆成功' % qq_)
        return self

    def like(self):
        if self.mode == KEYWORD:
            if self.keyword is not None:
                tid = self.__getTidByKeyword()
                if tid is not None:
                    self.__like(tid)
            else:
                print("请使用setKeyword()来设置关键字")

        elif self.mode == ALL:
            tids = self.__getTidsAll()
            self.__likeALL(tids)
        elif self.mode == KEYWORD_ALL:
            pass
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

    qq = 2037379421  # 被点赞的qq号
    keyword = 'keyword'  # 说说关键字，ALL模式下无需指定

    liker = QzoneLiker(qq, mode=ALL)  # 此模式为默认模式，无需设置keyword
    liker = QzoneLiker(qq, mode=KEYWORD).setKeyWord(keyword)  # 必须设置keyword
    # 单独登陆指定qq
    liker.login('10000', 'pwdpwdpwd')
    liker.like()
    # 可以批量处理指定配置文件中的qq号信息
    liker.likeBatch(conf)
