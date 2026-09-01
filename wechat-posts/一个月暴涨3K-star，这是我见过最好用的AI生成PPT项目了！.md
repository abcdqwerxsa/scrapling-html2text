# 一个月暴涨3K star，这是我见过最好用的AI生成PPT项目了！

**作者**: 开源先锋
**发布时间**: 2026-07-27 19:00
**原文链接**: https://mp.weixin.qq.com/s/_ulQ35ujteU991X-Z2an8A

---

* 戳上方蓝字“开源先锋”关注我

  

  

  

大家好啊，我是开源君！

做 PPT，大概是职场人逃不掉的苦差事。

你肯定经历过：内容早想清楚了，却卡在调格式、对齐、找模板上，一下午就耗进去了。

市面上不少 AI 做 PPT 的工具，要么生成一堆图片让你没法改，要么导出的文件死板、文字锁死。改都没法改，等于白做。

这就是今天这个项目 - `dashi-ppt-skill` 想解决的问题。![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c01.png)

## 项目简介

`dashi-ppt-skill`是一个给 AI Agent 用的 PPT 技能，它最实在的地方，是「产物即编辑器」。

![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c02.png)

生成的不是一张张图片，而是一个网页版 PPT 编辑器。你能翻页、点字就改、换图、调版式，打开就能用。

![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c03.gif)

硬核数字也不含糊：

  * 12 套视觉主题，覆盖各种场景和风格
  * 1020 个版式页面，每套主题都有独立的结构和视觉语言
  * 8576 个可调控件

6月开源以来已经收获了 4k+ star，采用 AGPL-3.0 开源协议，可自由使用甚至商用。

![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c04.png)  

## 功能特性

  * **01 浏览器里就能改**

![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c05.png)![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c06.png)

这是这个项目最大的亮点。每页自带控制台，二十多个维度可以调：滑杆调模块数量、换配色、换布局；点任意文字就地修改，装饰元素还会随字数自适应。改完自动保存，不用导出再改。

  * **02 真能导出可编辑 PPTX**

![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c07.png)![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c08.png)

不是截图，也不是死板图片。它逐节点还原，文字全部保持可编辑。你拿到的是一份真 PPT，扔进 PowerPoint 接着改都没问题。

  * **03 文字点击就改，媒体拖拽就换**

![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c09.gif)

任意一段文字，点一下就能就地编辑，装饰元素还会随字数自动适配。图片视频槽同理，点击或拖拽即可替换，上传自动压缩。文字资料里没配图的地方，系统会自动预留图片占位符，不用自己一页页找位置插图。

  * **04 12 套主题随时整套换**

![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c10.png)![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c11.png)![](https://r2.jeanjan.kdns.fr/pictures/img-b1126c6c12.png)

冷白调研风、色谱图表风、深蓝杂志风……风格不合心意？一句话让 Agent 整套换掉，不用重做。

  * **05 图表和分析模型齐全**

雷达图、瀑布图、矩形树图、漏斗、热力图、桑基图、甘特图应有尽有；SWOT、波特五力、PEST、商业模式画布、双钻模型这类专业版式也内置好了。

  * **06 内容零上传，安全放心**

文档和PPT内容不会发送到任何服务器，从生成、编辑到导出全在本机完成，成品离线也能打开。唯一联网的场景是首次安装依赖和一次静默版本检查，不涉及内容上传。

## 快速安装、使用

环境要求很简单：Node.js 20+ 和 npm，如果要导出 PPTX 或 PDF，本机还需要装有 Chrome、Chromium 或 Edge。

一键安装：
```

npx dashi-ppt-skill@latest  

```

国内网络环境可以用镜像加速：
```

npx --registry=https://registry.npmmirror.com dashi-ppt-skill@latest  

```

也可以直接让 AI Agent 帮你装，跟它说一句"帮我安装 skill：npx dashi-ppt-skill@latest"就行。

安装完之后，使用流程大致是这样：

  1. 跟 Agent 描述需求——主题、受众、页数、想突出的结论
  2. 从12套风格里选一个，顺便确认要不要配图配视频
  3. Agent 自动组稿，把需求整理成结构化内容并设计出PPT方案
  4. 在浏览器里随手编辑，改文字、换图片、调模块，改动自动保存
  5. 满意后导出想要的格式

也可以直接用命令行进行导出：
```

npm --prefix <project目录> run export:pptx -- <PPT输出目录>/ppt 输出.pptx  
npm --prefix <project目录> run export:pdf  -- <PPT输出目录>/ppt  

```

## 开源君想说

说实话，开源君第一次用`dashi-ppt-skill`的时候还有点不敢信。

把一份乱糟糟的文档丢给 Agent，摸会鱼的功夫，回来就有一份能直接翻页、点字改、还能导出成真 PPTX 的演示稿了。

它最打动我的，是把「做 PPT」从体力活变成了「说清楚你要什么」。

如果你也常被周报、汇报、路演折磨，可以亲手跑一套——反正开源、免费，本机就能用，试错成本几乎为零。

更多细节功能，感兴趣的可以到项目地址查看：
```

https://github.com/chuspeeism/dashi-ppt-skill  

```

推荐阅读：

[又一个神级 Skill 项目，狂揽2.8w star！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506601&idx=1&sn=d48d39c30f0f1a17504ccdd4e0166db6&scene=21#wechat_redirect)

[离线语音输入，开源免费，这也许是 windows 最好用的！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506626&idx=1&sn=0b0957c3b8c533914579a541f9bb17ba&scene=21#wechat_redirect)

[又来两个神级 skill，装了就不想删了！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506446&idx=1&sn=a34aea8a24ef477ceade98711273606b&scene=21#wechat_redirect)

[又来一个 8.8K 星 skill，感觉 Draw.io可以卸了！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506713&idx=1&sn=6b66cc3e1348ee2b6485c38a70aad60c&scene=21#wechat_redirect)

[两年实盘赚146万，跑赢标普500最多50个点，这个1.3 万 Star 项目真火！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506751&idx=1&sn=23ddb914fe7660a50a197b0f29824272&scene=21#wechat_redirect)

[又一个神级skill，一句话秒变架构图，能点能玩能交互！](https://mp.weixin.qq.com/s?__biz=MzkwNzU4NTMyMA==&mid=2247506826&idx=1&sn=224b9cb9e4771b6028b0ce2aa89cab23&scene=21#wechat_redirect)

  

  

  


