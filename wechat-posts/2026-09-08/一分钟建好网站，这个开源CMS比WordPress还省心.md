# 一分钟建好网站，这个开源CMS比WordPress还省心

**作者**: Prompt 工程队
**发布时间**: 2026-07-02 13:03
**原文链接**: https://mp.weixin.qq.com/s/NhkfwQfTWe4Bcgtr_jkvyg

---

PROMPT 工程队

做一个网站有多麻烦？ 

买个域名、租个服务器、装 WordPress、找主题、配插件、再对接表单服务、图床、统计分析……光是把这些东西凑齐，一个周末就没了。 

每个服务都有自己的账单、自己的后台、自己的宕机时间。**Instatic** 想把这件事简化到极致：一个 Bun 服务器，搞定建站的全部流程。 

![](https://r2.jeanjan.kdns.fr/pictures/img-b91700d801.jpeg)

01

一个 Docker 镜像，全部搞定 

git clone https://github.com/corebunch/instatic.git  
cd instatic  
INSTATIC_IMAGE=ghcr.io/corebunch/instatic:latest \  
docker compose -f compose.prod.yml \  
-f compose.sqlite.yml up -d 

然后打开 `localhost:5173`，跟着引导建站。没有 Nginx 配置，没有数据库初始化，SQLite 开箱即用。不想自己装？Railway 一键部署，两分钟上线。 

02

可视化编辑器，不是表单填空 

很多建站工具的"可视化编辑"其实就是个表单加预览窗口。Instatic 不一样，它的编辑器是一块**真正的画布** ——你可以把多个断点（桌面、手机）并排放，改一边另一边实时联动。需要精细操作的时候切到 live 模式，直接在真实页面上改。 

![](https://r2.jeanjan.kdns.fr/pictures/img-b91700d802.jpeg)

内置 Core Framework 设计系统，token 驱动配色/字号/间距

内置了 **Core Framework** 设计系统，颜色、字号、间距全是 token 驱动的。改一个变量，全站跟着变。不用写 CSS，不用打开开发者工具。 

03

AI 说一句话，直接在画布上盖出来 

Instatic 内置了一个 AI agent，不是那种生成截图糊弄你的——它**直接在画布上生成可编辑的节点** 。你跟它说"给我做一个产品落地页，左边放大图，右边放购买按钮"，它就真的用语义 HTML + CSS 搭出来，跟你手动拖的模块完全一样，随时可以改。 

支持自带模型：Claude、OpenAI、OpenRouter，或者本地 Ollama。你的 key 你的模型你的账单。 

![](https://r2.jeanjan.kdns.fr/pictures/img-b91700d803.jpeg)

组件系统：可复用的积木块，带类型参数和命名插槽

04

不止建站，还有表单、媒体、插件 

表单不用再接第三方服务了。Instatic 自己读表单字段、自动建表，提交的数据直接进你的数据库。媒体管理、审计日志、多用户权限、双因素认证，全内置。 

插件系统用 **QuickJS-WASM 沙箱** 运行，默认没有文件系统、没有网络访问。除非你主动授权某个域名，否则插件读不到你的任何数据。 

![](https://r2.jeanjan.kdns.fr/pictures/img-b91700d804.png)

后台仪表盘，12 列网格自定义布局

发布后页面直接烤成静态文件，没有框架运行时、没有水合步骤、没有数据库查询。访客拉到的是**干净到可以 view-source 的 HTML** 。 

05

早期项目，但方向对了 

有一说一，Instatic 现在还是 v0.0.x，功能很全但生态还在建。Real Analytics（站内统计）还没上，插件商店刚起步。不过它的架构思路——**一个服务器管全部、发布纯静态、AI 直接在画布上干活** ——确实是建站工具里没见过的方向。 

GitHub 三天前刚开源，已经冲上 Trending 榜 TypeScript 第二名。MIT 协议，没有付费层，没有功能锁定。 

● 项目地址  https://github.com/CoreBunch/Instatic 

每天发现一个好玩的开源工具  
欢迎关注 

