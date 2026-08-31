# 实测ego lite，给我Codex浏览器自动化加到2.5倍速了！

**作者**: 卡尔的AI沃茨
**发布时间**: 2026-07-30 18:04
**原文链接**: https://mp.weixin.qq.com/s/J_XtkE8zHBGOjyvGDHze8Q

---

## 很多人都好奇我一天烧几个亿token都是怎么烧的，

最近就是在不停迭代ai news radar这个AI热点网站，新的域名已经在路上了，并行在做的就是有没有一个便宜大碗的方案，让一些小模型也能做浏览器自动化，可以看到各个平台上博主们都在聊什么，什么工具突然火了被人提到了。

毕竟API都是烧钱啊。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79201.png)

前两天它给我推了一个新的浏览器自动化开源项目，ego lite，5.9k star，冲上github周榜了都。

用人话说，ego lite就是一个专门给AI Agent用的浏览器。Codex已经内置了一个类似的Chrome Use，我现在填ICP备案都可以全程GPT上传文件了。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79202.png)

但如果你跟我一样浏览器有多个账号的话，它属于是会经常弄错的那种，甚至是需要我在规则里面指定什么操作用账号A，什么操作用账号B之类的。

ego lite解决的就是这件事。

不是那种给Chrome套个插件，外面包一层自动化脚本的方案。它是一个基于 Chromium内核定制的独立浏览器，从底层就开始兼容人和Agent共用同一套浏览器环境的场景。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79203.png)

在用ego lite之前，我也折腾过几个别的方案。Browser-Use，Vercel的agent-browser这些我都试过，它们本质上是自动化框架，自己不带浏览器，得外挂一个来驱动，登录态搞起来很麻烦。

但ego lite因为它自己就是浏览器，还不绑死某个Agent，WorkBuddy，Claude Code，Codex都能直接接入。

核心就一句话，

让人和Agent共享同一个浏览器，但各自在自己的空间里干活。

WorkBuddy一键接入之后，效果是能直接对标别人的Browser和Web Use的。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79204.png)  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79205.png)

在WorkBuddy里，我先用了Playwright（另一个微软出的非常出名的浏览器自动化MCP，93.7k了）和ego lite跑了个简单的对比。

任务很简单，上GitHub Trending给我找今日 7 月 28 日的 Top 10项目。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79206.png)  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79207.png)

ego-browser耗时明显比Playwright短。

为了控制变量，我还对比了Claude Code的Claude-in-Chrome跟Codex的Control-Chrome，

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79208.png)

ego跑出来的速度要比Claude-in-Chrome快27秒。

![](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79209.png)  
  
![](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79210.png)

比Control-Chrome更是快了2.4倍。

![](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79211.png)

接下来就直接上压力，看下真实任务跑得怎么样。

  

Case 1，帮我把小号X上关注的博主全部扒一遍。

这是我测的第一个真实任务。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79212.png)

事情很简单，我想知道我在X上到底关注了哪些人，每个人的粉丝量和关注量分别是多少。

但X的Following页面只显示头像和名字，不显示粉丝数。要看每个人的粉丝量，得一个一个点进去看。

所以我让Workbuddy通过ego-browser skill来帮我做。

在说结果之前，先额外岔开说说一个让我觉得体验很爽的点。

ego lite的做法是在同一个浏览器里开了多个独立的Space。每个Space就是一个隔离的工作区，互相独立互不干涉，Agent做的事跟你毫无关系。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79213.jpeg)

更爽的是，首次启动的时候ego lite会问你要不要迁移Chrome 的Cookie，扩展，书签和Profile。迁移完之后Agent就直接复用你的登录态了，不用每个网站重新登一遍。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79215.png)

当然了，能用你的登录态也就代表它的权限比较高。还是建议第一次用的时候可以先用独立Profile测测，涉及付款，删除，发布这类敏感操作，最好还是保留人工确认的步骤。

回到这个case。

整个过程大概是这样的，ego-browser在ego lite里开了一个Space，打开了我的X Following页面。因为之前迁移过Chrome的登录态，直接就是我的账号状态，不用重新登录。

然后它开始自动往下滑，把账号全部加载出来，再逐个提取每个人的Following和Followers数据。我在另一个Space里继续干我的工作。真的，就是很字面意思的互不打扰。

随便挑几个看看准不准，

Sam Altman，565万粉丝

Elon Musk，2.41亿粉丝

Anthropic，居然只有155万粉丝

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79216.png)

我又手动去X上抽查了几个小号，数据也都对得上。

这整个任务，从我下达指令到拿到完整的CSV和Markdown表格，中间完全不需要我插手。ego-browser自己处理了滚动加载，页面跳转，数据提取这些操作，我就是最后看了一眼结果。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79217.png)

  

第二个case我想了个更离谱的操作。

在用Codex的朋友应该都知道，Codex的API额度和ChatGPT网页版的额度是分开算的。你在网页版里跟ChatGPT聊天，让它联网搜索，这些不消耗你的订阅额度，不走API。

那问题来了，如果我正在用Codex跑一个需要联网搜索的任务，我能不能不用Codex 自己去烧token做搜索，而是让它打开ChatGPT网页版，在那边搜完，把结果带回来？

答案是可以的。ego-browser 能做到这件事。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79218.png)

而且平时Agent操作浏览器的时候，要么就是把整个HTML丢给模型，要么就是不停地截图再识别。HTML一丢就是几万个Token，截图识别又经常认错元素，来来回回烧的钱比任务本身还多。

ego lite做了一个叫Snapshot的东西，不吃截图不需要完整代码，直接从浏览器内核层面直接提取页面的结构化信息，哪里有按钮，哪里有输入框，哪里有可以点的链接，整理成一份精简的说明交给 Agent。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79219.png)

传给模型的上下文量一下子就降下来了。

我实际测的时候还发现，一些嵌套iframe比较深的页面，传统方案经常抓不到里面的内容，ego lite的Snapshot能覆盖到。这点在处理一些后台管理系统，第三方嵌入组件这类复杂页面的时候体感更加明显。

回到这个case。

整个过程大概 5 分钟不到。ego-browser照样是在ego lite里开了个Space，照样是打开ChatGPT网页版（因为登录态迁移过了，直接就是登录状态），输入问题，等ChatGPT联网搜索完毕，再把结果整理好带回来。

拿到的结果质量还挺不错的，ChatGPT用High模式做了完整的联网检索，整理出了一份带数据、带来源链接的10条清单。

同样的做法，在WorkBuddy里也是能做到的，对模型要求不高。

而且很多Agent网页端的credit都不算在通常的coding plan额度里，不用白不用，四舍五入就是直接省钱了。

  

Case 3，终极任务小某书

我就这样说难度吧，一般的浏览器自动化Skill连帖子都打不开。

我还给ego故意挑了一个难的，还是从WorkBuddy走。某书是出了名的对Agent不友好。不登录连搜索结果都看不到，页面各种动态加载，内容结构也复杂。很多传统的自动化方案一到小红书就直接趴窝，要么卡在登录页面，要么抓到的是空白页。

所以我特别想看看ego lite在小某书上能不能跑通。

提示语也简单，去小某书上搜搜我自己，翻一翻主页，看看最火的几条内容是哪些。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79220.png)

ego-browser在ego lite里打开小某书，一开始弹了个登录弹窗，但因为之前迁移过Chrome的登录态，它实际上是已登录状态，关掉弹窗就直接进去了，很爽，不需要扫码。

搜索，进主页，翻列表，整个流程都很顺畅。

这里面有个细节值得说一下。

小红书的帖子列表是虚拟列表，你往下翻的时候，上面的内容会从页面里被移除掉，不是简单地「滚到底就能看到全部」。

ego-browser处理得很聪明，它一边滚一边把数据存下来，最后拼出了完整的列表，一共采集到了251篇帖子。

然后它还能进到每篇帖子的详情页，把点赞，收藏，评论这些数据一个个抓出来。我手动抽查了几条，数据都是对的。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79221.png)  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79222.png)  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79223.png)

小某书在各个渠道爬取时挺容易被风控的，限制特多特杂。

但是在ego lite里因为是真的浏览器操作，体感是真的相对安全的，而且也没有跳验证码人工验证。

最后，说到这里就不得不提速度了。

ego lite的Agent操作方式也不一样，不是传统的发一条CLI指令→看一次结果→再发一条指令的来回循环，是让Agent直接写一段JavaScript脚本，把多个操作步骤组合在一起一次性执行。

用人话说就是，传统方案像聊天一样一条一条发消息，ego lite更像写一封邮件把事情一次说清楚。

我自己跑下来体感确实快了不少，尤其是多步骤的复杂自动化任务，以前Agent要来来回回十几轮才能搞定的事，现在几轮就结束了。

GitHub仓库里也有一组对比数据，跟Vercel的agent-browser比，复杂任务最快能到2.6倍速。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79224.png)

用几天后我就有点好奇，

这个团队到底是在浏览器外面套了一层壳，还是真的在改浏览器内核？

查了一下发现，从Citro Labs的资料来看，这团队里的成员甚至参与过Chromium上游的代码贡献，比如CSS shape-outside对path()和shape()的实现，这部分已经合入Chromium主线，随Chrome 149 发布了。Google I/O 2026也把CSS shape()列为了重点能力之一。林林总总也有了近500个补丁被合并进Chromium。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79225.png)

怪不得这帮人上来就能搞浏览器内核。。。

OK聊完体验，说说怎么装，这部分特别简单。

ego lite目前只支持macOS，Windows和Linux还在规划中。

去官网lite.ego.app 下载一个dmg，装上就行。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79226.png)

我装完打开的时候它自动扫描了我电脑上的Agent工具，检测到了Claude Code和Codex，然后自动把ego-browser这个skill装好了。

我什么都没配，直接就能用。

之后我在Claude Code里跑任务，只要涉及到浏览器操作，它就会自动调用ego-browser skill，启动ego lite来干活。整个过程零配置，这点我觉得做得挺好的。

  
![Image](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79227.png)

最后的最后，

ego lite现在还处在很早期的阶段，

现在Agent是已经可以写代码，做分析，生成内容，参与决策。但还是需要Skill，MCP等辅助它们去打开网页，登录系统，查看后台和跨页面操作时。

ego lite是有在认真给Agent提供一个可理解，可操作，还低干扰的浏览器环境。

不占用屏幕，

不额外烧Token，

不需要全程盯着它干活。

稳稳地，

很放心。

@ 作者 / 卡尔 & yc星辰

最后，感谢你看到这里👏如果喜欢这篇文章，不妨顺手给我们 _点赞｜在看｜转发｜评论 📣_

如果想要第一时间收到推送，不妨给我个星标🌟

如果你有更有趣的玩法，欢迎在评论区聊聊🤝

更多的内容正在不断填坑中……

![](https://r2.jeanjan.kdns.fr/pictures/img-e84ba79229.jpeg)

