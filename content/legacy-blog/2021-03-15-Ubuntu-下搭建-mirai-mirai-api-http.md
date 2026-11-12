---
title: Ubuntu 下搭建 mirai + mirai-api-http
date: '2021-03-15T13:04:44.000Z'
lastmod: '2021-03-15T13:32:31.768Z'
weight: 2
categories:
- 旧博客（算法竞赛）
aliases:
- /2021/03/15/Ubuntu-下搭建-mirai-mirai-api-http/
original_url: https://bakapiano.github.io/2021/03/15/Ubuntu-下搭建-mirai-mirai-api-http/
original_generator: Hexo
migrated_from: rendered HTML
---

## mirai {#mirai}

提供 QQ Android 协议支持的高效率机器人库

[mirai](https://github.com/mamoe/mirai)

## 使用 iTXTech MCL Installer 获取 mcl {#使用-iTXTech-MCL-Installer-获取-mcl}

[iTXTech MCL Installer](https://github.com/iTXTech/mcl-installer)

新建目录

```dos
mkdir mcl
cd mcl
```

根据系统和架构选择对应文件：[release](https://github.com/iTXTech/mcl-installer/releases)

```awk
curl -LJO https://github.com/iTXTech/mcl-installer/releases/download/2827601/mcl-installer-2827601-linux-amd64
chmod +x mcl-installer-2827601-linux-amd64
./mcl-installer-2827601-linux-amd64
```

无特殊需求可一路回车，mcl就装好啦

## 使用 mcl 安装 mirai-api-http {#使用-mcl-安装-mirai-api-http}
```jboss-cli
./mcl --update-package net.mamoe:mirai-api-http --channel stable --type plugin
```

测试 http api：

```perl
./mcl
login qq号 qq密码
```

如果要求滑块验证请看下一步

## 手动完成滑动验证 {#手动完成滑动验证}

参考自 [mirai-login-solver-selenium](https://github.com/project-mirai/mirai-login-solver-selenium)

退出控制台，在 mirai 运行时中添加 JVM 属性 mirai.slider.captcha.supported 以启用手动验证

修改文件 mcl `vim mcl` 为如下内容：

```bash
#!/usr/bin/env sh
export JAVA_BINARY="/root/mcl/java/bin/java"
$JAVA_BINARY -Dmirai.slider.captcha.supported -jar mcl.jar $*
```

再次打开 mcl 并登录，用有桌面系统的电脑打开验证地址

F12 打开 DevTools，切换运行模式为 Android

![pic1](/images/legacy-external/7f60cc2b0c31-img1.png)

切换到 Console，复制 [captcha.inject.js](https://github.com/project-mirai/mirai-login-solver-selenium/blob/master/src/main/resources/mirai-selenium/captcha.inject.js) 的内容全部复制至 Console 中并运行

![pic2](/images/legacy-external/28e477807dae-img2.png)

复制传回的 ticket 并在 mcl 中输入，流程正确的话就能完成登陆了

![pic3](/images/legacy-external/4c542388e31e-img3.png)

## 验证 api {#验证-api}

使用了 python sdk [Graia Application](https://github.com/GraiaProject/Application)

安装：

```applescript
pip install graia-application-mirai
```

运行 Python 代码：

```python
from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.application.message.chain import MessageChain
import asyncio

from graia.application.message.elements.internal import Plain
from graia.application.friend import Friend

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host="http://localhost:8080", # 填入 httpapi 服务运行的地址
        authKey="0123456789", # 填入在setting.yml中设置的authKey
        account=88888888, # 你的机器人的 qq 号
        websocket=True # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)

@bcc.receiver("FriendMessage")
async def friend_message_listener(message: MessageChain, friend: Friend, app: GraiaMiraiApplication):
    msg = message.asDisplay()
    if msg.startswith(".help"):
        await app.sendFriendMessage(friend, MessageChain(__root__=[Plain(".help\t显示帮助指令\r\n.copy\t复读")]))
    elif msg.startswith(".copy "):
        msg = msg[6:]
        await app.sendFriendMessage(friend, MessageChain(__root__=[Plain(msg)]))
    else:
        await app.sendFriendMessage(friend, MessageChain(__root__=[Plain("收到!")]))

app.launch_blocking()
```

最后尝试给机器人发消息，收到回复就测试成功了
