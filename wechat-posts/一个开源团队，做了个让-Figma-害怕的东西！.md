# 一个开源团队，做了个让 Figma 害怕的东西！

**作者**: 开源先锋
**发布时间**: 2026-06-23 19:00
**原文链接**: https://mp.weixin.qq.com/s/-dovEXFVQbmmizp5Gq6DYQ

---

* 戳上方蓝字“开源先锋”关注我

  

  

各位好啊，我是开源君！

在设计协作领域，Figma 几乎成了代名词。但数据存在别人服务器上、按人头付费的模式，对一些团队来说，始终是个不大不小的顾虑。

肯定有很多朋友一直在关注有没有更好的选择，最近发现的一个叫 `Penpot`的项目，也许就会是你感兴趣一直想找的。

## 项目简介

`Penpot`是一款为设计师和开发者打造的、可自托管的开源 UI 设计协作工具。UI 界面设计、交互原型制作、团队实时协作、设计系统管理……这些 Figma 能做的，它基本都能做。

更关键的是，它基于 SVG、CSS、HTML 等开放标准构建，设计稿本身就是可以直接读懂的代码，不存在私有格式锁定的问题。![](https://r2.jeanjan.kdns.fr/pictures/img-49084fbe01.png)

项目由西班牙公司 Kaleidos 开发的开源设计与协作平台，最早作为内部项目孵化，2021 年正式转型为面向大众的开源产品对外发布。

目前，Penpot 在 GitHub 上已收获超过 **52.9k Star** ，发布版本 80余个，活跃度相当高。项目采用 MPL-2.0 开源协议，既可以在官方云端直接使用，也可以自己部署到私有服务器上。

![](https://r2.jeanjan.kdns.fr/pictures/img-49084fbe02.png)

## 功能特色

### 01 UI 设计：线框图、原型、响应式布局一站搞定

很多设计工具只能画"好看的静态稿"，但 Penpot 不一样。

![](https://r2.jeanjan.kdns.fr/pictures/img-49084fbe03.png)

从最早期的线框图，到可交互的原型，再到响应式界面，Penpot 把整个 UI 设计流程都覆盖了。尤其是它把 CSS Flex 和 Grid 布局直接内嵌进设计工具，你在画布上拖出来的布局，底层就是真实的 CSS 结构——设计稿就是规则，不是一张死图。

### 02 设计系统：组件、Design Tokens、共享库，规模化不慌

团队大了之后，最头疼的就是设计不一致——按钮颜色这里一个、那里一个，字体大小各说各话。

![](https://r2.jeanjan.kdns.fr/pictures/img-49084fbe04.png)

Penpot 从根子上解决这个问题。它原生支持 Design Tokens，颜色、字体、圆角、间距这些设计变量统一定义，设计和开发共用一份，改一处、全局更新。组件库也可以跨项目共享，一套设计系统覆盖整个产品线，维护起来省心很多。

### 03 AI 工作流：把 AI 直接接进设计核心

这是 Penpot 近期最让人眼前一亮的方向。

![](https://r2.jeanjan.kdns.fr/pictures/img-49084fbe05.png)

它不是简单加了个"AI 生成图片"按钮，而是开放了整个 AI 集成通道——任何 AI Agent、任何大模型、任何 AI 工具，都可以直接接入 Penpot 的核心流程，驱动"代码生成设计稿""设计稿生成代码""设计稿生成设计稿"等工作流。MCP Server 的支持让 AI 工具真正能读懂、能操作设计文件。

### 04 代码协作：设计稿和代码，真的能对上

设计师和开发者最经典的矛盾，就是"我画的是这样，你实现的是那样"。

![](https://r2.jeanjan.kdns.fr/pictures/img-49084fbe06.png)

Penpot 用开放标准从源头解决了这个问题。它以 SVG 作为原生文件格式，CSS、HTML、SVG、JSON 全部开放，开发者在代码检查面板看到的样式，就是可以直接用的代码，不需要二次翻译。文件格式也是开放的，不怕被私有格式锁死。

## 快速安装、使用

Penpot 提供两种使用方式，按需选择：

**方式一：直接用官方云端版（推荐新手）**

直接访问 `https://design.penpot.app`注册账号，免费，打开浏览器就能用，零配置。

**方式二：Docker 自托管（推荐团队/企业）**

确保本地已安装 Docker 和 Docker Compose，然后执行：
```

# 下载官方 docker-compose 配置  
curl -o docker-compose.yaml https://raw.githubusercontent.com/penpot/penpot/main/docker/images/docker-compose.yaml  
  
# 启动服务  
docker compose -p penpot -f docker-compose.yaml up -d  

```

服务启动后，浏览器访问 `http://localhost:9001` 即可打开 Penpot 界面。

默认需要注册第一个账号作为管理员。注册完成后就可以创建团队、新建项目，开始设计了。

更详细的配置（如 SMTP 邮件、存储路径、反向代理）可以参考官方文档：https://help.penpot.app/technical-guide/getting-started。

![](https://r2.jeanjan.kdns.fr/pictures/img-49084fbe07.png)

建议服务器配置：4 核 8GB 内存起步，可支撑 10～20 人团队同时协作。

## 开源君想说

说实话，第一次打开还是有点学习成本——毕竟和 Figma 的操作习惯不完全一样，找功能需要适应一下。但慢慢熟悉之后，反而会发现它在"设计与开发打通"这件事上想得比 Figma 更彻底。

Penpot 最值钱的地方，不只是"免费"，而是它把数据主权还给了你，把工具控制权还给了团队。

如果你的团队正在用 Figma 但对订阅费和数据安全有顾虑，或者想搭一套自己可控的设计工具链，Penpot 绝对值得花半天时间认真试试。

更多细节功能，感兴趣的可以到项目地址查看：
```

https://github.com/penpot/penpot  

```

推荐阅读：

[狂揽2.8w star，NotebookLM 没开放的功能，它做到了！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247505804&idx=1&sn=0f0947929c8d87e78f00418b48fd6300&scene=21#wechat_redirect)

[微软新开源项目6啊，终端报错不用再到处搜、复制粘贴了！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247505956&idx=1&sn=8752063232f1cee17abb31298c21b4cf&scene=21#wechat_redirect)

[一句话生成可上线的动效，这个项目真不错！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506113&idx=1&sn=6d40ee7c6e04c2442ec521aaa8bf585c&scene=21#wechat_redirect)

[Github 霸榜的 2 个视频项目，一个比一个离谱！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506228&idx=1&sn=a4c45cfb95e804822e34953e51d5c6d0&scene=21#wechat_redirect)

[仅 4MB 大小，因看不惯某付费软件开发，牛皮！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506118&idx=1&sn=e8511b9488525d2d4ecf35e255f2a561&scene=21#wechat_redirect)

  

  

  


