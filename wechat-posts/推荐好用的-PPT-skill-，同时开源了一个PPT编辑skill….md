# 推荐好用的 PPT skill ，同时开源了一个PPT编辑skill…

**作者**: 数字Q
**发布时间**: 2026-06-30 11:53
**原文链接**: https://mp.weixin.qq.com/s/6mWiXclGmAYrsMflZIZHsQ

---

让 AI 帮我做 PPT 这件事，已经从噱头变成日常了。用 PPT skill，让Agent帮我出幻灯片，出来的效果会比原生的好很多。

用了一圈下来，市面上的 PPT skill 其实分成了几派，各有所长。但有一个共同的痛点，HTML我编辑不了啊。

## 先说市面上有哪些好用的 PPT skill

我按"技术路线"分了三类。

### 第一类：HTML 网页 PPT

这一派生成的是单文件 HTML，浏览器直接全屏放映，视觉表现力是所有方案里最强的。

归藏的 **guizang-ppt-skill** 是我自己很爱用的。两条风格线：电子杂志风（衬线 + WebGL 流体背景， _Monocle_ 那种高级感）和瑞士国际主义风（无衬线 + 网格点阵 + IKB/柠檬黄/安全橙）。杀手锏是预设了一套很硬的版式规范，正文页锁死 22 种注册版式（S01-S22），AI 不会乱发明结构，一致性很高。

![](https://r2.jeanjan.kdns.fr/pictures/img-4de79fde01.png)

lewislulu 的 **html-ppt-skill** 走"主题丰富"路线，24 套主题、31 种版式、20 多种动画，想要什么风格基本都能找到现成的。

![](https://r2.jeanjan.kdns.fr/pictures/img-4de79fde02.png)

zarazhangrui 的 **frontend-slides** 卖点是"show, don't tell"：不让你用文字描述审美，而是先生成 3 个视觉预览让你挑。预设了 10 套风格（Neon Cyber / Paper & Ink / Brutalist 等），还主打"反 AI 味"，明着反对紫色渐变白底那种通用审美。另外它能把现有 `.pptx` 转成网页版。

![](https://r2.jeanjan.kdns.fr/pictures/img-4de79fde03.png)

### 第二类：原生 PPTX

这一派生成真正的 `.pptx`，PowerPoint 直接打开。

hugohe3 的 **ppt-master** 是这里面我最佩服的。最大的不同是生成原生形状和动画，不是贴图片糊弄，每个文本框、色块都是真元件，能在 PowerPoint 里点开改。还能把演讲者备注转成语音旁白，套你自己的 `.pptx` 模板。

![](https://r2.jeanjan.kdns.fr/pictures/img-4de79fde04.png)

**baoyu-slide-deck** （宝玉的）走另一条路，生成图片型幻灯片，AI 先出大纲分镜再逐页生成图片。视觉极其精致，代价是拿到手是图片，没法编辑。适合"我要一套好看的成品去演示"，不适合"我还要改字"。

![](https://r2.jeanjan.kdns.fr/pictures/img-4de79fde05.png)

### 第三类：HTML 和 PPTX 之间的桥梁

**huashu-design** （花叔的）野心更大，定位是 HTML 原生设计 skill，幻灯片只是能力之一，带了 20 条设计哲学和一套 5 维评审标准，还能导出 MP4。这种"既要网页表现力，又要能落地成视频"的思路，代表了 HTML PPT 这条路的天花板能到哪。

![](https://r2.jeanjan.kdns.fr/pictures/img-4de79fde06.png)

## 这些方案都很强，但有一个共同的痛点

**生成的时候很爽，改的时候很崩溃。**

尤其是 HTML PPT 这一派。AI 帮你生成了一份漂亮的网页幻灯片，放出来一看，标题里有个错别字，或者第三页数字填错了，或者你觉得这页标题再往左挪一点就好了。

这时候你的选择只有两个。

要么回去找 AI 重新生成。可重新生成一版，整个布局可能都变了，你原来满意的细节全没了。为了改一个字，赌上整套版面。

要么自己打开 HTML 去手改代码。但这种 skill 背后是一大坨 CSS 变量、vw/vh 自适应单位、WebGL 着色器、翻页脚本。就算你是前端，对着别人写的一大坨代码找一个字号该改哪行，也是折磨。

这就很拧巴。生成能力的进步，反倒把"微调"这件事衬托得更原始了。

原生 PPTX 那一派（ppt-master 那种）倒是没这个问题，生成的就是真元件，双击能改。但代价是视觉表现力被 PowerPoint 本身的天花板卡死了，做不出网页那种效果。

## 那编辑这一环怎么办

既然生成派已经这么强了，我不去凑这个热闹，去补另一环：**让任何已经生成好的 HTML PPT，能被可视化微调。**

它不是生成器，是个"后处理"工具。流程是这样：你随便用上面哪个 skill 生成一份 HTML PPT，把这份文件喂给它，它会吐出一个"可编辑版"。双击打开，不用按任何键，直接进编辑模式。

![](https://r2.jeanjan.kdns.fr/pictures/img-4de79fde07.png)

你能做的事：单击选中，双击改文字（可以改单个字，不是整段替换），拖本体挪位置，右侧面板改字号/字重/颜色/行高/宽高（数字框加滑动条加方向键）。还能复制、删除、上下调换组件。

改完有两个出口。点"导出纯净版"，下载一份没有编辑器代码的干净 HTML，原文件所有脚本和自适应都不破坏。点"全屏预览"，遮罩全屏看效果，满意了再回来。

为什么做成 skill 而不是单独的软件？我的感觉是，skill 是活的。大模型能自己判断这份 HTML 是什么结构、该调哪个工具，而且能一直迭代。做成软件就死了，遇到搞不定的网页，就是搞不定。

它只解决"改"，不解决"生"。所以你还得先有一份 HTML PPT。要做PPT的话推荐你用上面的几个skill，确实好用。

如果你也常用 HTML PPT，又被"改一个字得求 AI 重生成"折磨过，欢迎来试试。

**NQ-PPT-HTML-Editor**

开源在 https://github.com/Natural-Q/NQ-PPT-HTML-Editor

## 相关链接

文中提到的 PPT skill，地址都放这：

  * **guizang-ppt-skill** ：https://github.com/op7418/guizang-ppt-skill

  * **html-ppt-skill** ：https://github.com/lewislulu/html-ppt-skill

  * **frontend-slides** ：https://github.com/zarazhangrui/frontend-slides

  * **ppt-master** ：https://github.com/hugohe3/ppt-master

  * **baoyu-slide-deck** ：https://github.com/JimLiu/baoyu-skills/tree/main/skills/baoyu-slide-deck

  * **huashu-design** ：https://github.com/alchaincyf/huashu-design  


