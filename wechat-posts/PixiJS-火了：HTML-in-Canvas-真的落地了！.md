# PixiJS 火了：HTML-in-Canvas 真的落地了！

**作者**: 前端开发爱好者
**发布时间**: 2026-06-23 08:33
**原文链接**: https://mp.weixin.qq.com/s/CSbc9iKMvF57ByBMLNHHew

---

前段时间我写过一次 `HTML-in-Canvas`，当时很多人的第一反应是：**这个提案确实疯狂，但感觉离真正落地还很远** 。

结果没想到，**PixiJS 先动手了。**

![](https://r2.jeanjan.kdns.fr/pictures/img-4ed6318501.png)

在最新的 `PixiJS v8.19.0` 中，官方已经加入了 `HTML-in-Canvas` 相关支持，新的能力叫：
```

pixi.js/html-source  

```

简单说就是：**PixiJS 现在可以把真实` DOM` 元素渲染成 `texture`，再放进自己的 `GPU` 渲染体系里。**

因为长期以来，Web 前端其实一直有两个割裂的世界：`DOM` 适合写 **UI、文本、布局、表单、交互** ；`Canvas / WebGL / WebGPU` 适合做 **高性能渲染、游戏、可视化、特效和复杂动画** 。

问题是，两边都很强，但很难真正融合。

你想在 `Canvas` 里画一个漂亮的 UI 面板，往往不能直接写 `HTML`，而是要自己处理文本、坐标、换行、状态、事件、缩放、输入框、按钮反馈，基本等于重新造一层 UI 渲染引擎。

**PixiJS 这次更新，真正有意思的地方就在这里：它开始把这两个世界接起来了。**

## ` HTML` 真的可以变成 `PixiJS` 纹理了

`PixiJS` 这次新增的核心能力是：
```

HTMLSource  
ElementImageSource  

```

其中 `HTMLSource` 用来处理实时 `DOM`，`ElementImageSource` 更偏向静态快照。

官方给出的思路很直接：你可以创建一个普通 `HTML` 元素，把它作为 `PixiJS texture` 的资源，然后通过 `Sprite.from()` 放进舞台。

![](https://r2.jeanjan.kdns.fr/pictures/img-4ed6318502.gif)

简化一下，大概是这样：
```

import { Application, Sprite } from'pixi.js';  
import { HTMLSource } from'pixi.js/html-source';  
  
const app = new Application();  
  
await app.init({  
resizeTo: window,  
});  
  
document.body.appendChild(app.canvas);  
  
const form = document.createElement('form');  
  
form.innerHTML = `  
  <input value="still editable" />  
`;  
  
app.canvas.appendChild(form);  
  
const sprite = Sprite.from(  
new HTMLSource({  
    resource: form,  
    autoUpdate: true,  
  })  
);  
  
app.stage.addChild(sprite);  

```

重点不是这几行代码，而是它背后的变化：
```

form 依然是真实 DOM  
但 PixiJS 可以把它当成 texture 使用  

```

更关键的是，这不是传统的截图，也不是 `html2canvas` 那种模拟渲染，更不是各种 `SVG hack`。

它依赖的是浏览器层面的 `HTML-in-Canvas` 能力，让真实 `DOM` 的渲染结果进入 `Canvas / GPU` 管线。

官方也提到，输入框仍然可以编辑，链接仍然可以点击，`CSS animation` 也可以继续运行。

也就是说，这不是一张死图，而是一个仍然保留浏览器交互能力的 `DOM`，同时又能被 `PixiJS` 当作纹理参与渲染。

**这就非常离谱了。**

## ` Canvas` 写 UI，最痛苦的地方开始松动了

只要真正用 `Canvas` 做过 UI，就知道它有多麻烦。

画一个矩形很简单，做一个按钮也不难，但当你开始做复杂 UI，问题会瞬间爆炸：

  * 文本要怎么换行？
  * 中文、英文、`Emoji` 混排怎么办？
  * 字体加载完成前后如何同步？
  * 输入框怎么做？
  * 光标怎么闪？
  * 滚动区域怎么处理？`hover`、`focus`、`disabled`、`selected` 这些状态要不要自己维护？
  * 屏幕阅读器怎么读？
  * 移动端缩放和 `DPR` 怎么处理？

这也是为什么很多 `Canvas` 项目最后都会变成一种很别扭的结构：
```

Canvas 负责主画面  
DOM 浮在 Canvas 上面  
两边靠坐标同步  

```

这种方案不是不能用，但只要项目稍微复杂一点，就会出现一堆边界问题。

比如 `Canvas` 缩放了，`DOM` 位置要同步；`Canvas` 做旋转或滤镜了，`DOM` 跟不上；你想截图或导出，`DOM` 不在画布里；你想把 UI 放进 `WebGL` 场景当贴图，`DOM` 又没法真正进入渲染链路。

`HTML-in-Canvas` 的价值就在这里。

它不是让你继续手写一套 **UI** ，而是让你用浏览器最成熟的方式写 **UI** ：
```

<div class="panel">  
  <h2>Player Info</h2>  
  <input value="PixiJS" />  
  <button>Start</button>  
</div>  

```

然后把这个 `DOM` 渲染结果交给 `Canvas / WebGL / WebGPU` 使用。

换句话说：
```

HTML 负责布局和交互  
PixiJS 负责渲染和合成  

```

**这才是这次更新真正硬核的地方。**

##  一些已经出现的用法

虽然 `HTML-in-Canvas` 目前还在实验阶段，但它的使用场景已经非常明确了。

  * **游戏 UI** （HTML 写界面 + Canvas 渲染）
  * **数据可视化** （图表 + HTML 标签）
  * **海报生成** （直接导出）
  * **WebGL / 3D UI** （HTML 作为纹理）
  * **设计工具** （富文本 + 实时渲染）

这也是为什么 `PixiJS` 现在接入 `HTML-in-Canvas`，会显得这么关键。

## 为什么 `PixiJS` 要先接这个能力？

因为 `PixiJS` 不是普通 `Canvas` 工具库，它本身就是一个成熟的 2D 渲染引擎，长期面向 Web 游戏、互动广告、创意页面、数据可视化、编辑器、实时动画这些场景。

这些场景天然需要两种能力：
```

一边要高性能图形渲染  
一边要复杂 UI 和文本排版  

```

过去只能二选一，或者强行把 `DOM` 和 `Canvas` 拼在一起。

`PixiJS` 现在接入 `HTML-in-Canvas textures`，其实是在尝试一种新的分工方式：
```

DOM 负责它最擅长的：布局、样式、输入、交互、语义  
PixiJS 负责它最擅长的：渲染、动画、滤镜、合成、GPU 管线  

```

这个分工一旦跑通，对前端图形应用非常有价值。

比如你可以让一个 `HTML` 表单作为 `PixiJS` 场景中的一个 `Sprite`，然后对它做位移、缩放、滤镜、混合模式，甚至把它和粒子、遮罩、后处理效果一起合成。

以前这类需求不是不能做，但实现成本极高，而且经常伴随大量 `hack`。现在，浏览器底层开始提供能力，`PixiJS` 这类图形引擎开始做封装。**这个信号比 API 本身更重要。**

##  顺手一提：`PixiJS` 这次还拥抱 `AI Agent` 了

除了 `HTML-in-Canvas`，`PixiJS` 6 月更新里还有一个很值得关注的点：官方发布了 **25 个 `PixiJS Agent Skills`**。

这批 `skills` 面向 `Claude Code`、`Cursor`、`Codex`、`Copilot`、`Windsurf` 这类 AI 编程工具，作用很直接：**教 AI 正确使用` PixiJS v8`，少生成过时的 `v7` 写法。**

安装命令也很简单：
```

npx skills add https://github.com/pixijs/pixijs-skills  

```

从 `v8.19.0` 开始，这些 `skills` 还会直接随 `pixi.js` npm 包发布，安装后可以在：
```

node_modules/pixi.js/skills/  

```

里面找到。

这件事和 `HTML-in-Canvas` 放在一起看，其实更有意思。

`PixiJS` 这次不是单纯做 API 更新，而是在同时适配两个方向：
```

一个是下一代 Web 渲染能力  
一个是下一代 AI 编程工作流  

```

前者解决“浏览器能不能把 `HTML`、`Canvas`、`GPU` 打通”，后者解决“AI 能不能正确写现代 `PixiJS` 代码”。

**这就不是普通发版了。**

##  写在最后

`PixiJS` 这次支持 `HTML-in-Canvas`，短期看还是实验功能；但长期看，它代表的方向非常清晰：
```

DOM 不再只是页面结构  
Canvas 不再只是像素画布  
HTML 有机会进入 GPU 渲染链路  

```

过去我们说 `Canvas` 很强，但做 UI 太原始；`DOM` 很好用，但进不了图形渲染系统。

如果你在做 Web 游戏、数据可视化、互动页面、`WebGL` 场景、设计工具、海报编辑器，或者任何需要复杂图形渲染的前端项目，`PixiJS` 这次更新都值得看一眼。

它不一定马上改变日常业务开发，但它很可能代表一个新方向：
```

用 HTML 写界面  
用 PixiJS 驱动渲染  
用 GPU 完成合成  

```

**这才是前端渲染最疯狂、也最值得期待的地方。**

  * **相关文档** ：`https://pixijs.com/blog/june-2026`


