# 又一个神级 skill ,  狂揽 3 万 Star。

**作者**: 开源日记
**发布时间**: 2026-09-07 14:22
**原文链接**: https://mp.weixin.qq.com/s/47Zx51RxjU6CSXiXEOt3dg

---

  

  

大家好，我是熊叔，今天继续逛 GitHub。

大家在用 Codex 写东西的时候，应该会发现一个比较明显的问题。

让它们写代码，现在已经很顺手了。

但是只要让它顺便画一张架构图、流程图，画出来的东西经常一眼就是“AI 出品”。

几个圆角方框，加几根箭头，再配上蓝紫渐变。

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f01.png)

内容虽然没有错，但是放在文章、方案或者项目文档中，总觉得差点意思。

今天我在 GitHub 上看到了一个项目，就是用来解决这个问题的。

它叫 **Diagram Design** 。

它没有重新做一个在线绘图软件，而是直接把一套画图规则做成了 Skill，装进 Claude Code、Codex 这些 Agent 里面。

以后要画图的时候，直接对它说你想表达什么就可以。

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f02.png)![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f03.png)![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f04.png)

## 先决定画什么图

我比较喜欢这个项目的一点，是它没有把“画图”理解成简单地往页面里塞方框。

目前项目已经准备好了39种图形类型。

架构图、流程图、时序图、状态机、ER 图这些开发里常见的都有。

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f05.png)

还有甘特图、泳道图、桑基图、鱼骨图、看板、用户旅程、Wardley Map、部署图、依赖关系图、UML Class、数据库 Schema。

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f06.png)

基本上写技术文章和项目文档会遇到的场景都涵盖了。

比如你告诉 Codex：

“画一张系统架构图，前端连接 API，API 后面有 PostgreSQL 和 Redis。”

它会先判断这里适合用Architecture，而不会随便找一些框来拼接。

如果业务逻辑里有判断分支，就会换成 Flowchart。

如果重点是几个服务之间调用的先后顺序，就用 Sequence。

先选择好图，然后开始画，这个思路我觉得比单纯提供模板靠谱得多。

## 它还会主动删东西

这个项目里有一句设计原则，我挺认同：

**一张图不是东西放得越多越好。**

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f07.png)

翻译一下就是：

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f08.png)

它给图设置了复杂度限制。

一个节点要表达出一个明确的信息，不需要的连接线直接删除，颜色只保留一两个真正重要的地方。

当节点很多的时候，它还会建议把图分成两个。

这个细节很关键。

我们自己画架构图的时候也容易犯这样的毛病，觉得东西没放全，就把数据库、接口、缓存、消息队列等等全塞到一张图里去。

最后的信息是齐全了，但是看图的人却不知道从哪里开始看。

Diagram Design 实际上就是帮你把信息整理一遍。

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f09.png)

## 不是固定的一套配色

如果只是准备几十套漂亮模板，我觉得这个项目也没什么特别的。

它真正实用的地方就是可以读取你自己的网站品牌样式。

比如说我有一个网站，可以告诉Agent：

`onboard diagram-design to https://xxx.com`

它会读取网页中的背景色、正文颜色、强调色和字体，并将这些信息映射到自己的 Style Guide 中。

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f10.png)

后面生成的新图就会自动使用这套风格。

也就是说，公司内部做文档，可以统一成公司的颜色。

自己写博客也可以和网站视觉保持一致。

而且这套样式不仅会影响一张图，后面的39张图也会跟着一起变化。

这样比每次在Prompt中都写上“背景用什么颜色、标题用什么字体、节点边框多粗”要方便得多。

## 最后直接得到 HTML 和 SVG

生成结果也很简单。

Diagram Design 最终输出的是一个独立 HTML，图本身使用 SVG。

不需要Figma，也不需要安装其它的绘图软件。

HTML 直接浏览器打开就能看。

想放到网页里，可以继续用 SVG。

写公众号或者文档的时候也可以直接截屏或者导出为PNG。

项目还提供了Light、Dark和FullEditorial三种静态风格，可以先打开自带的Gallery看一下效果，再选择自己喜欢的一种。

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f11.png)

## Codex 两条命令就能装

平时使用Codex的话，可以直接在插件市场里安装：
```

codex plugin marketplace add cathrynlavery/diagram-design  
codex plugin add diagram-design@diagram-design  

```

Claude 也支持：
```

/plugin marketplace add cathrynlavery/diagram-design  
/plugin install diagram-design@diagram-design  

```

另外 Pi、OpenCode 以及其他兼容 Agent Skills 的工具也能使用。

装完之后，再让 Agent 画架构图、流程图，就不只是简单地“生成一张图”了。

它会先选好图形类型，再按照设计规则去控制布局、颜色、节点数量和重点。

我觉得这才是这个项目真正有意思的地方。

以前我们总是想着怎么把 Prompt 写得更详细一些，这样 AI 才能画得更漂亮一些。

Diagram Design 用另外一种方式：

**干脆把怎么画图这件事，本身做成一套 Skill 交给 Agent。**

平时经常使用Claude、Codex来写技术文档，或者需要画出架构图、流程图的朋友可以试一试。

项目地址：https://github.com/cathrynlavery/diagram-design

平时我会持续地分享一些有趣的开源项目，有兴趣的朋友可以关注一下。

可以回复关键词，找到你想要的项目。

![](https://r2.jeanjan.kdns.fr/pictures/img-20d3790f12.png)

