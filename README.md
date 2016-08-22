# qzonelib
qq空间爬虫库

### 简介
该项目为qq空间方面的爬虫程序


### 主要功能
此版本暂时只包括qq空间的说说点赞功能，有其他功能功能需要可在issue中提出。


### 注意事项
* 该项目中的登陆部分使用到了 <a href="https://github.com/gera2ld/qqlib">qqlib</a> 来实现，需要提前安装该项目
* 该项目基于3.5.2开发，目测支持python2.x python3.x


### 使用方法
#### qzoneliker 现包括两种点赞模式：
1. ALL : 为指定qq号的所有说说点赞
2. KEYWORD ：为指定qq号，包含指定关键字的最近一条说说点赞


#### example
* 使用单个指定qq号登陆
```python 
    qq = 10001  # 被点赞的qq号
    keyword = 'keyword'  # 说说关键字，ALL模式下无需指定
    
    # 两种点赞模式，二选一即可，默认为ALL
    liker = QzoneLiker(qq, mode=ALL)  # 此模式为默认模式，无需设置keyword
    liker = QzoneLiker(qq, mode=KEYWORD).setKeyWord(keyword)  # 必须设置keyword
    
    # 单独登陆指定qq
    liker.login('10000', 'password') # 设置用于登陆点赞的qq号信息
    # 调用点赞方法
    liker.like()    
```
* 使用配置文件批量导入qq点赞
```python
  
    # 配置文件格式为 ：
    #       qq号:密码
    #  如:  10000:password
    # 不同的qq号用换行隔开
    
    # 设置qq号配置文件路径，多qq批量点赞
    conf = 'qqlist.ini'
    qq = 10001  # 被点赞的qq号
    keyword = 'keyword'  # 说说关键字，ALL模式下无需指定

    # 两种点赞模式，二选一即可，默认为ALL
    liker = QzoneLiker(qq, mode=ALL)  # 此模式为默认模式，无需设置keyword
    liker = QzoneLiker(qq, mode=KEYWORD).setKeyWord(keyword)  # 必须设置keyword
    
    # 调用批量点赞，使用配置文件中的qq号为被点赞的qq号的说说点赞
    liker.likeBatch(conf)

```
