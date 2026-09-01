# 两个"隐形浏览器"正面交锋：CloakBrowser vs camofox-browser

**作者**: 赶走坏脾气
**发布时间**: 2026-06-05 07:29
**原文链接**: https://mp.weixin.qq.com/s/byJX2o2aewnbGOv61Gg5wA

---

  

## 你用过 Playwright 吗？那你一定被"人机验证"恶心过

我之前写过一个浏览器自动化项目，用 [Playwright](https://mp.weixin.qq.com/s?__biz=MzI2NjQxOTE5Ng==&mid=2247485534&idx=1&sn=bdf02b7c5ddb69f20a20e6ccee02fe9c&scene=21#wechat_redirect) 控制 Chromium 做数据采集。脚本写得挺漂亮，一跑起来——Cloudflare 的挑战页就弹出来了。改 UA、加延迟、用 stealth 插件，折腾了一整天，该拦还是拦。后来甚至试了更极端的方案：用 undetected-chromedriver，结果不几天又被新规则封了。

后来我才搞明白：问题不在你的脚本写得不够像人，而在于**浏览器本身就在出卖你** 。

普通 Chromium 会暴露 CDP（Chrome DevTools Protocol）痕迹，navigator.webdriver 属性为 true，Canvas 指纹、WebGL 渲染器信息、AudioContext 指纹全是"自动化"特征。反检测平台对这些信号门儿清，看见就拦。你以为加了 random delay 就像人了？检测平台看的是鼠标移动轨迹的曲率、键盘按键间隔的标准差，这些你根本模拟不了。

解决方案只有一个：**从 C++ 源码层面改浏览器的指纹** 。不是 JS 层面的 patch，不是 plugin，是直接改编译后的二进制文件。

最近 GitHub 上有两个项目把这事做到了极致。一个叫 CloakBrowser，23k+ 星；另一个叫 camofox-browser，6k+ 星。我用了一周，说说我的看法。

## CloakBrowser：Chromium 阵营的反检测王者

CloakBrowser 的定位很明确：**一个能通过所有机器人检测的 Chromium 浏览器** 。

它的做法是在 Chromium 源码里打了 58 个 C++ 补丁，覆盖了你能想到的所有指纹维度——Canvas、WebGL、Audio、字体列表、GPU 信息、屏幕分辨率、WebRTC、网络时序、自动化信号、CDP 输入行为。说白了，它不是一个"在 Chrome 外面套一层伪装"的工具，而是**从骨头里改过的 Chrome** 。

### 58 个补丁意味着什么？

市面上大部分反检测方案（包括 Puppeteer 的 stealth 插件）都在 JavaScript 层面做文章。JS 层 patch 有个致命问题：检测平台总能找到绕过方式。比如你 patch 了 navigator.webdriver，检测平台换一种方法检测 CDP 端口是否开放。

CloakBrowser 直接在 C++ 层面改，检测平台拿到的指纹本身就是"干净"的。这就好比——JS 层 patch 是给嫌疑人戴个面具，C++ 层 patch 是直接换了一张脸。

### 三行代码切换

我最喜欢 CloakBrowser 的一个设计：**它是 Playwright 和 Puppeteer 的 drop-in 替换** 。

`# 之前  
from playwright.sync_api import sync_playwright  
  
# 之后  
from cloakbrowser import CloakBrowser  
  
browser = CloakBrowser(humanize=True)  
page = browser.new_page()  
`

Python 和 JavaScript 都支持，`pip install cloakbrowser` 或 `npm install cloakbrowser` 一键安装。不需要手动下载二进制文件，它会自动管理 Chromium 版本（目前基于 Chromium 146）。

### humanize=True：一键拟人

这个参数很巧妙。开启后，鼠标移动会走贝塞尔曲线而不是直线，键盘输入有真实的人类时序偏差，滚动行为也有随机模式。

最硬核的数据是：开启 humanize 后，**reCAPTCHA v3 评分达到 0.9** 。0.9 是什么概念？真人操作的平均水平就是 0.9。也就是说，连 Google 自己的人机验证都分不清它是人还是机器。

它通过了 30 多个检测站点的测试，包括 Cloudflare Turnstile、FingerprintJS、BrowserScan、Pixelscan。MIT 协议开源。

### 配置管理器

CloakBrowser 还带了一个 GUI 配置管理器，叫 CloakBrowser Manager。功能类似 Multilogin 或 AdsPower——可以管理多个浏览器配置文件，每个配置文件独立保存 cookies 和 localStorage。支持代理设置和 GeoIP 自动匹配时区/语言。

如果你做多账号运营，这个功能很实用。不同账号对应不同的代理 IP、时区、语言环境，反检测平台一检查——嗯，这个用户确实在纽约，时区是 EST，语言是英语，完全合理。

对了，CloakBrowser 同时支持 headless 和 headed 模式。headless 跑在服务器上做批量采集，headed 模式做调试，灵活切换。

## camofox-browser：给 AI Agent 量身定做的浏览器

如果说 CloakBrowser 是"让 Chromium 变隐形"，那 camofox-browser 的思路完全不同——它是"**给 AI Agent 用的浏览器服务** "。

底层引擎是 Camoufox，一个 Firefox 的 fork，同样做 C++ 级指纹修改。但 camofox-browser 在 Camoufox 之上包了一层 REST API，设计目标不是"让爬虫通过反检测"，而是**让 AI Agent 能高效地操控浏览器** 。

说白了，它根本不在乎你是不是能骗过 reCAPTCHA。它的重点是：Agent 怎么才能又快又稳地完成浏览器操作任务。

### 核心设计理念：不是给你用的

这个项目 GitHub 描述的第一句就很有态度："Anti-detection browser server **for AI agents** "。

传统浏览器的交互方式是操作 DOM——找到元素、点击、输入。但 DOM 很重，一个页面可能几十万节点。camofox-browser 用的是**无障碍快照（accessibility snapshots）** ，只保留页面中有意义的语义信息，体积比 HTML 小约 90%。

配合稳定的元素引用机制（e1, e2, e3...），AI Agent 拿到的是一个简洁、稳定、不会因为 CSS 变化而失效的交互界面。这点对 AI Agent 来说太重要了——DOM 会变，但语义结构相对稳定。

### 搜索宏系统

camofox-browser 内置了十几个搜索宏：`@google_search`、`@youtube_search`、`@reddit_subreddit`、`@twitter_search` 等。AI Agent 不需要自己写搜索逻辑，直接调用宏就行。

YouTube 字幕提取也集成好了（通过 yt-dlp），Agent 可以直接获取视频内容。

### 轻到离谱的资源占用

这是我最惊讶的数据：**空闲时内存占用约 40MB** 。

一个完整的 Firefox 浏览器实例，带反检测、带 REST API、带 VNC 支持，空闲只要 40MB。这意味着它可以跑在树莓派上，可以跑在 5 美月的 VPS 上，可以在共享基础设施里同时开很多个实例。

Docker、Fly.io、Railway 都支持一键部署，还有 noVNC 支持交互式登录（比如先手动登录某个账号，后续 Agent 就可以用这个 session）。

### OpenClaw 原生支持

作为 OpenClaw 用户，这条让我很兴奋——camofox-browser 有官方的 OpenClaw 插件支持。也就是说，我的 AI Agent 可以直接通过 OpenClaw 调用 camofox-browser 的能力。不需要自己写集成代码，开箱即用。

### 结构化提取

另一个我觉得很实用的功能是结构化提取。你可以定义一个 JSON Schema，camofox-browser 会把页面中的数据按照 Schema 映射到 snapshot refs 上。做数据采集的同学应该懂这意味着什么——不需要写 XPath，不需要写 CSS selector，直接声明你要什么数据就行。

## 正面对比

我把两个项目的关键维度拉了个表：

| 维度           | CloakBrowser             | camofox-browser    |
|--------------|--------------------------|--------------------|
| 底层引擎         | Chromium 146             | Firefox (Camoufox) |
| 反检测方式        | 58 个 C++ 补丁              | Camoufox C++ 指纹修改  |
| 核心定位         | 通用反检测浏览器                 | AI Agent 专用浏览器服务   |
| API 形式       | Playwright/Puppeteer SDK | REST API           |
| 交互方式         | DOM 操作                   | 无障碍快照 + 元素引用       |
| 拟人行为         | humanize=True（贝塞尔鼠标等）    | 无（Agent 不需要）       |
| reCAPTCHA 评分 | 0.9                      | 未公开                |
| 通过检测数        | 30+                      | 未公开                |
| 内存占用         | 标准 Chromium 水平           | ~40MB（空闲）          |
| 安装方式         | pip / npm                | Docker / npm       |
| 配置管理         | CloakBrowser Manager GUI | REST API           |
| 星标数          | 23,858                   | 6,315              |
| 许可证          | MIT                      | MIT                |

## 选哪个？看你的场景

这两个项目不是竞品，准确地说，它们服务的是不同的场景。

**选 CloakBrowser 的情况：**

  * 你在做数据采集、爬虫、自动化测试

  * 你需要通过 Cloudflare、reCAPTCHA 等反机器人检测

  * 你习惯用 Playwright 或 Puppeteer

  * 你需要 headless 模式批量运行

  * 你需要管理多个浏览器配置文件

**选 camofox-browser 的情况：**

  * 你在构建 AI Agent，需要浏览器能力

  * 你希望 Agent 通过语义化方式操控浏览器，而不是操作 DOM

  * 你的运行环境资源有限（树莓派、廉价 VPS）

  * 你需要多实例并行运行

  * 你是 OpenClaw 用户，想要开箱即用的浏览器集成

**都选的情况：**

说实话，这两个项目的技术路线不冲突。CloakBrowser 解决的是"怎么让浏览器不被检测到是自动化"，camofox-browser 解决的是"怎么让 AI Agent 高效地使用浏览器"。如果你在构建一个完整的 AI Agent 系统，完全可以**底层用 camofox-browser 做 Agent 交互，需要更高反检测能力时再切换到 CloakBrowser** 。

还有一种更常见的组合：用 CloakBrowser 做数据采集（它有最硬的反检测能力），用 camofox-browser 做 Agent 决策和页面理解。两者通过 API 组合在一起，各司其职。

## 我的看法

反检测浏览器这个赛道，过去几年一直是灰色地带。Multilogin、AdsPower 这些商业产品价格不菲，技术原理也不透明。

CloakBrowser 和 camofox-browser 都选了开源路线，MIT 协议，技术方案都基于 C++ 源码级修改——这是目前公认最可靠的反检测方案。不是 JS patch 那种猫鼠游戏，而是从根基上解决问题。

CloakBrowser 的 23k 星和 0.9 reCAPTCHA 评分证明了一件事：**开源方案完全可以做到商业级别的反检测效果** 。

camofox-browser 的 agent-first 设计理念则代表了另一个趋势：**浏览器正在从"给人用的工具"变成"给 AI 用的服务"** 。无障碍快照替代 HTML、REST API 替代 DOM 操作、40MB 内存支持树莓派——这些设计选择都指向一个方向，AI Agent 需要的浏览器，和人类需要的是完全不同的东西。

这个方向，值得持续关注。

两个项目的 GitHub 链接：

  * CloakBrowser: https://github.com/CloakHQ/CloakBrowser

  * camofox-browser: https://github.com/jo-inc/camofox-browser


