# OpenClaw 永久免费的提取任何网页的终极方案

**作者**: 石臻说AI
**发布时间**: 
**原文链接**: https://mp.weixin.qq.com/s/EwVItQH4JUsONqv_Fmi4wQ

---

⭐ 设为星标 · 第一时间收到推送

![](https://mmbiz.qpic.cn/sz_mmbiz_png/TkWsojtosvS5MrZrVNLUSdpjm8ibzY4HjKfIia0YJULAe4smjqia9zPicQ1LOqmDbwOMxuNric6WAicO7twAbrponRXc9pwTz1lkUFdIaXLgungzo/640?from=appmsg)石臻说AI 编辑：石臻 **导读：** 用 AI 写文章，最大的隐藏成本不是模型调用次数，而是每次抓网页时塞进去的 token。今天做了一次完整的实测，对比了 Jina、Scrapling、web_fetch 三个方案——发现差别大到出乎意料。

## 问题是怎么暴露的

在用 AI 做内容创作时，流程大概是这样的：找到一篇参考文章 → 读取全文 → AI 消化后写稿。

`web_fetch` 是最直接的工具，给一个 URL 就返回内容。但用着用着发现不对：

  * 一篇普通技术博客，轻松返回 8000-15000 token
  * 遇到 GitHub README 或文档页，可能更多
  * 一篇文章采集 3-5 个信息源，光读内容就烧掉几万 token



更麻烦的是，`web_fetch` 返回的是整个页面，包括：导航栏、侧边栏、页脚、广告、"相关推荐"……真正有用的正文可能只占 30%。

## 三个方案的实测对比

拿了一篇 Substack 文章做测试：《How I Dropped Our Production Database》，同条件（max 12000字符）横向对比三种提取方式。

### 方案一：Jina Reader

用法：
```


web_fetch("https://r.jina.ai/原始URL", maxChars=30000)

```


Jina 是专门做网页内容提取的服务，会自动渲染页面、抽取正文、去掉导航和广告，返回干净的 Markdown。

实测效果：
```


Title: How I Dropped Our Production Database and Now Pay 10% More for AWS

I'm working on expanding the [AI Shipping Labs website](https://aishippinglabs.com/) ...

My gradual plan was:

```

    1.   Move the current static site from GitHub Pages to AWS S3
    2.   Move DNS to AWS so the domain is fully managed there
```
...

```


标题、正文、链接、图片、列表——格式全保留，干净利落。速度约 1.4 秒。

**缺点：每天免费限额 200 次。** 高产时期两三天就能跑完。

### 方案二：web_fetch 直接抓
```


web_fetch(url, maxChars=30000)

```


测试同一篇文章——直接报错：`fetch failed`。

Substack 有反爬机制，web_fetch 根本进不去。对于 Medium、部分付费博客、微信公众号，同样的问题。

即使是能抓到的页面，返回的也是全页 HTML 转 Markdown，噪音多、token 浪费严重。

**结论：只适合静态页面（GitHub README、普通技术博客），不适合有反爬的主流平台。**

### 方案三：Scrapling + html2text

Scrapling 是一个开源 Python 爬虫框架（GitHub: D4Vinci/Scrapling），项目定位是"为现代 Web 设计的自适应爬虫"。核心特性：

  * **原生绕过反爬** ：StealthyFetcher 能绕过 Cloudflare Turnstile 等主流反爬系统，不需要额外配置
  * **自适应选择器** ：网站改版导致 selector 失效时，能自动重新定位元素，不需要手动维护
  * **零依赖启动** ：`pip install scrapling`，没有复杂的浏览器驱动配置

![](https://mmbiz.qpic.cn/sz_mmbiz_jpg/TkWsojtosvQHMX1ATdZjGcyeX0V6hYicDFCia7126MnVd9RXtAfribMh5Q4ibC02pkmqJAAENBt344mxxViaUKPAe0qdqvic1aZVRSO56dAqJwxz0/640?wx_fmt=jpeg)![Scrapling GitHub 项目主页（24.9k Star）](https://mmbiz.qpic.cn/mmbiz_png/TkWsojtosvQ8yZS6HZ5yVOc2p90DW6ttF6IMEbd2M9aK4QtfSrqDHialiaeiaqcIYc5A0xxcyuiagTGHShKd0IELsicub07nic5XsTsDWLx8ZLq3U/640?from=appmsg)

用法：
```


python3 scrapling_fetch.py <url> 30000

```


脚本逻辑：

  1. 1用 `Fetcher.get()` 拿到页面 HTML
  2. 2按优先级尝试正文选择器：`article → main → .post-content → [class*="body"]`
  3. 3找到正文后，用 `html2text` 把 HTML 转成 Markdown
  4. 4截断到指定字符数



实测效果：
```


# How I Dropped Our Production Database and Now Pay 10% More for AWS

### A Terraform command executed by an AI agent wiped the production infrastructure...

I'm working on expanding the [AI Shipping Labs website](https://aishippinglabs.com/) ...

```

    1. Move the current static site from GitHub Pages to AWS S3
    2. Move DNS to AWS so the domain is fully managed there
```
...

```


和 Jina 几乎一样干净，标题层级、链接、图片 URL、列表都保留了。速度约 3 秒，**无限制，不需要 API Key** 。

![三种方案提取效果对比](https://mmbiz.qpic.cn/sz_mmbiz_png/TkWsojtosvRAxNotSbMepwafgzSEg07DW7jat5Tc2r6UFpUSdKSEUGr9FIJDP9dBs0YybCQwUviciaNG3JflB1XicT4icYAibDUTH4NcRo5ffBqk/640?from=appmsg)

## 意外发现：微信公众号文章

测试微信公众号链接（`mp.weixin.qq.com`）时：

  * Jina → 直接 403 拦截，内容为空
  * web_fetch → 请求被中断
  * **Scrapling → 完整拿到正文，Markdown 格式，图片链接也保留**



微信公众号有专门的反爬，Jina 和 web_fetch 都进不去，但 Scrapling 的 `StealthyFetcher` 能绕过去。

这个发现意义很大——之前我们读公众号文章要么靠搜索工具（只能拿摘要），要么靠浏览器渲染（慢且复杂），现在一行命令就能拿全文。

微信公众号文章：Scrapling 直接能拿全文，Jina 403，这一条就值得把 Scrapling 装上。

## 最终推荐策略

经过实测，确定了这套分级策略：

| 优先级 | 方案              | 适用场景                    | 限制     |
|-----|-----------------|-------------------------|--------|
| 1   | Jina Reader     | 大部分英文博客、Substack、Medium | 200次/天 |
| 2   | Scrapling       | Jina 超限、微信公众号、反爬平台      | 无限制    |
| 3   | web_fetch       | 静态页面、GitHub、技术文档        | 全页噪音多  |
| 4   | Browser Firefox | 需要登录态、极端反爬              | 最慢     |



**域名快捷路由：** `mp.weixin.qq.com` 直接用 Scrapling，跳过 Jina，不浪费配额。

**关于 maxChars：** 统一设 30000，既保证完整正文，又不会塞爆 context。

## 坑：Scrapling 必须配合 html2text

最开始用 Scrapling 时，直接调 `get_all_text()` 提取文本，以为可以省事。结果发现：
```


How I Dropped Our Production Database and Now Pay 10% More for AWS A Terraform command executed by an AI agent wiped the production infrastructure...

```


纯文字流，段落消失，链接消失，图片消失，标题层级消失。对 AI 写稿来说，链接和图片 URL 都是有价值的素材——引用图片、追溯信息源都要用。

正确做法是先拿 `html_content`，再用 `html2text` 转换：
```


import html2text
h = html2text.HTML2Text()
h.ignore_links = False
h.ignore_images = False
h.body_width = 0  # 不自动折行
md = h.handle(element.html_content)

```


这一步加上去，输出就和 Jina 一样干净了。

  * **Jina** ：最好用，格式最干净，但每天 200 次限额
  * **Scrapling + html2text** ：效果和 Jina 相当，无限制，能读微信公众号（Jina 做不到）
  * **web_fetch** ：有反爬的平台直接失败，只适合静态页面
  * **maxChars 统一设 30000** ：省 token 的同时保留完整正文
  * **微信公众号直接走 Scrapling** ，不要浪费 Jina 配额



**🦞 获取完整 Skill 文件**  
关注公众号「石臻说AI」，回复「scrapling」获取本文完整的 OpenClaw Skill 配置文件和 scrapling_fetch.py 脚本。  
进群交流：回复「进群」加入**小龙虾养殖交流群** ，和更多 OpenClaw 用户一起折腾 AI 自动化。

参考链接

  * Scrapling GitHub：https://github.com/D4Vinci/Scrapling
  * Jina Reader 文档：https://jina.ai/reader
  * html2text PyPI：https://pypi.org/project/html2text

📚 往期精选 [一个人搞定整个营销团队：AI Agent 自动化获客的 10 个实战玩法](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247498257&idx=1&sn=547f0a4c295116130278566c1d39a4aa&scene=21#wechat_redirect) [Claude Code 官方最佳实践：10 条拿来就能用的技巧（来自 Claude Code 作者亲测）](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247498556&idx=1&sn=b60a3312020c7494a0bef08c99186107&scene=21#wechat_redirect) [Token 省 89%、成功率 97.9%：Google 的 WebMCP 要把浏览器 Agent 从「瞎摸」变成「直连」](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247497806&idx=1&sn=3f4661e99c0f70f266926dd7154c03aa&scene=21#wechat_redirect) [我用 AI 一周赚了 500 万](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247498255&idx=1&sn=f03ec2f73f644c789ecc7fac3bab60d6&scene=21#wechat_redirect) [Anthropic 官方 Claude Code 使用指南：10个内部团队的真实用法，附完整 PDF](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247498072&idx=1&sn=46225f650ba62687db66f51c20a9c35a&scene=21#wechat_redirect) [OpenClaw用这26个提示词变身超级助理](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247498254&idx=1&sn=f865e7231ea7887b0241ac56400a4e36&scene=21#wechat_redirect) [AI 成功了，然后世界崩了——一份来自 2028 年的经济尸检报告](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247498321&idx=1&sn=10a3820c701a028887a6ea5d11d8dbea&scene=21#wechat_redirect) [Chatbot时代结束了？在百度智能云一键部署OpenClaw，AI真的能炒股了](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247497750&idx=1&sn=4d49781d9f1384129b884da23986493c&scene=21#wechat_redirect) [一句话，让三个 AI 同时开工：OpenAkita 开源多 Agent 助手解析](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247498727&idx=1&sn=a6efd85f68ef932d4502f33b21f9b1f3&scene=21#wechat_redirect) [用了10年显示器，这是我第一次觉得“这是专门为我做的“](https://mp.weixin.qq.com/s?__biz=Mzg4ODY1NTcxNg==&mid=2247498851&idx=1&sn=d5949ab1e516513c05273c7f04f3c5f4&scene=21#wechat_redirect)

* * *

— **完** —

**围观朋友圈查看每日最前沿AI资讯**

![二维码](https://mmbiz.qpic.cn/mmbiz_jpg/kmWVxLDDVAUIIacP7klkMlRmmOaT3TnlIuS57YkwUT0s5ItIDjYaCGSrG8fnYYKrsIx6pyKpsFVibib0vx2ic5Ttg/640?wx_fmt=jpeg)

**一键关注 👇 点亮星标**

**每日科技资讯和提效工具分享**

