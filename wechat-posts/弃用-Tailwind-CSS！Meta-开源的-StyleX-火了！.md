# 弃用 Tailwind CSS！Meta 开源的 StyleX 火了！

**作者**: 前端开发爱好者
**发布时间**: 2026-07-04 08:33
**原文链接**: https://mp.weixin.qq.com/s/T10qSObkUQUEtX9jPU5_vw

---

前端样式方案，又开始卷起来了。

这两天看到一个很有意思的动态：

Meta 新开源了一套设计系统`Astryx`，底层用的就是`React` 和`StyleX`。

![](https://r2.jeanjan.kdns.fr/pictures/img-676aaf0801.png)

更关键的是，像`Linear` 这种非常讲究产品质感和工程质量的团队，也已经开始逐步转向`StyleX`。

![](https://r2.jeanjan.kdns.fr/pictures/img-676aaf0802.png)

这就让`StyleX` 一下子变得很微妙。

因为这几年，`Tailwind CSS` 几乎已经成了前端写样式的默认答案。

写页面快、改样式快、不用想命名，直接在`className` 里堆工具类，效率确实高。

但问题也很明显：项目小的时候，`Tailwind` 很爽；项目一大，`className` 开始变长，条件样式开始变乱，组件复用开始变绕。等到设计系统复杂起来，主题、变量、类型约束、样式覆盖，又会变成新的麻烦。

这时候，**Meta** 开源的`StyleX` 就重新被推到了台前。

而且被定义为**Tailwind 最大对手。**

##  StyleX 最近真的很火

这次`StyleX` 重新被讨论，不只是因为**Meta** 开源了它，而是因为**Meta** 已经把它放进了自己的新组件体系里。

Meta 新开源的`Astryx`，底层就是基于`React` 和`StyleX` 构建。

![](https://r2.jeanjan.kdns.fr/pictures/img-676aaf0803.png)

它不是一个简单的`Button`、`Input`、`Modal` 组件集合，而是一套面向现代 UI 工程的设计系统。

官方对`Astryx` 的定位很有意思：
```

AI fluent fully customizable without dependencies
```

简单说就是：**AI 友好、完全可定制、无依赖。**

这就很有意思了。以前我们看一个组件库，更多关注的是：按钮好不好看，弹窗好不好用，主题能不能改，暗色模式支不支持。但`Astryx` 明显不只是想做一套 UI 组件，它想做的是一套新的 UI 基础设施。

人能用。

**AI Agent** 也能用。

这点非常关键。因为现在前端开发已经变了，以前组件库主要服务人类开发者，文档写清楚、API 好理解、主题能改就够了。

但未来越来越多**UI** 代码，可能会由**Agent** 生成。

这时候组件库要考虑的不只是：
```

人能不能看懂
```

还要考虑：
```

AI 能不能稳定生成 AI 能不能理解约束 AI 能不能按设计系统写出正确 UI AI 能不能少写一堆乱七八糟的样式
```

所以`Astryx` 背后最值得看的，不只是组件数量，而是它选择了什么样的样式底座。

答案就是：`StyleX`。

同时，`Linear` 也在真实项目里迁移到`StyleX`。这里要说准确一点，Linear 公开文章里写的是 **从`styled-components` 迁移到`StyleX`**，不是直接从`Tailwind` 迁移。但这件事依然很有代表性。

因为 Linear 这类团队看中的不是语法新不新，而是：
```

运行时成本能不能降下来 样式合并能不能更可预测 组件边界能不能更清楚 设计系统能不能长期维护 迁移能不能通过工具自动化推进
```

这才是`StyleX` 真正值得关注的地方。它不是为了让你少写几行 CSS，而是为了让大型前端项目的样式系统，不至于几年之后彻底失控。

## StyleX 到底是什么？

![](https://r2.jeanjan.kdns.fr/pictures/img-676aaf0804.png)

`StyleX` 是 Meta 推出的一套样式系统，主要面向大型复杂 UI。官方对它的定位是：

**expressive、type-safe、composable、predictable、themeable**

大致意思就是：写起来灵活，有类型提示，能组合，结果稳定，还能做主题系统。

它的写法大概是这样：
```

import * as stylex from'@stylexjs/stylex';  
  
const styles = stylex.create({  
card: {  
    padding: 16,  
    borderRadius: 12,  
    backgroundColor: 'white',  
  },  
active: {  
    backgroundColor: 'black',  
    color: 'white',  
  },  
});  
  
function Card({ active }) {  
return (  
    <div {...stylex.props(styles.card, active && styles.active)}>  
      StyleX  
    </div>  
  );  
}  

```

乍一看，有点像`styled-components`、`Emotion` 这类 CSS-in-JS。

但底层完全不一样。

传统 CSS-in-JS 最大的问题，是运行时成本。组件渲染时要计算样式、插入样式、维护样式表，项目越大，性能和调试压力越明显。

`StyleX` 的思路是：

**写的时候像 CSS-in-JS，打包的时候变成静态 CSS。**

它会在构建阶段把样式提取出来，生成静态 CSS 文件。运行时基本只负责合并`className`，不会像老派 CSS-in-JS 那样疯狂插入`<style>`。

这才是它真正狠的地方。

## 它和 Tailwind 最大的区别

`Tailwind` 的核心是：
```

工具类优先
```

你直接在 JSX 里写：
```

<div className="p-4 rounded-xl bg-white text-black"> Hello </div>
```

好处是快，所见即所得，写页面非常爽。

但缺点也很直接：当组件复杂之后，`className` 会越来越长，条件样式会越来越乱，设计系统里的语义也容易被打散。

而`StyleX` 的核心是：
```

组件样式优先
```

样式仍然跟组件放在一起，但不是直接堆字符串，而是通过`stylex.create()` 定义样式，再通过`stylex.props()` 组合使用。

这带来几个明显变化：
```

Tailwind：样式写在 className 里 StyleX：样式写在 JS 对象里 Tailwind：靠工具类组合 StyleX：靠编译器生成原子 CSS Tailwind：更适合快速写页面 StyleX：更适合大型组件系统 Tailwind：写法自由，约束较少 StyleX：写法更工程化，约束更强
```

所以`StyleX` 不是简单替代`Tailwind`。

它更像是 Meta 给大型前端项目准备的一套样式工程方案。

## 为什么 Meta 要自己造？

因为**CSS** 在大项目里真的很难管。

小项目里，**CSS** 问题不明显。

几个页面、几十个组件，随便写都能跑。

但到了 Meta 这种体量，问题会被无限放大：**全局样式污染、选择器冲突、优先级战争、无效 CSS 堆积、主题系统混乱、组件复用困难。**

最典型的就是**CSS** 优先级问题。

很多项目写到后面都会出现这种情况：
```

.card .title {  
color: red;  
}  
  
.page.card.title {  
color: blue;  
}  
  
.app.page.card.title {  
color: black !important;  
}  

```

一开始只是覆盖一下，最后变成选择器军备竞赛。

谁选择器更长，谁赢。

谁加了`!important`，谁赢。

而`StyleX` 要解决的就是这个问题。

它通过编译器生成无冲突的原子 CSS，并且规定：
```

最后应用的样式永远生效
```

也就是说，样式覆盖逻辑变得非常可预测，不再靠猜选择器权重。

这点对大型团队非常重要。因为一个样式系统最怕的不是写不出来，而是维护几年之后没人敢改。

## 真正的核心：编译型 CSS-in-JS

我觉得`StyleX` 最重要的价值，不是语法，而是它背后的路线。

过去前端样式大概经历了几轮变化：
```

传统 CSS ↓ Sass / Less ↓ CSS Modules ↓ CSS-in-JS ↓ Tailwind / Atomic CSS ↓ Zero-runtime CSS-in-JS
```

`StyleX` 站的就是最后这个位置。

它既想保留 CSS-in-JS 的组件化写法，又想避免 CSS-in-JS 的运行时性能问题。所以它选择用编译器解决问题。

开发时你写的是 JS 对象：
```

const styles = stylex.create({ root: { display: 'flex', padding: 16, color: 'red', }, });
```

构建后，它会被拆成原子 CSS：
```

.x1 { display: flex; }  
.x2 { padding: 16px; }  
.x3 { color: red; }  

```

多个组件如果用到了相同规则，最终可以复用同一个原子类。

这就很像`Tailwind` 的产物。

区别在于：

**Tailwind 是你手写原子类，StyleX 是编译器帮你生成原子类。**

这个差异非常关键。手写原子类适合快速开发，但编译器生成原子类更适合做大型工程约束。

## StyleX 强在哪里？

第一，**没有运行时样式注入** 。

这意味着它不像传统`CSS-in-JS` 那样，在运行时不断生成和插入样式。最终产物是静态 CSS，浏览器直接加载，性能路径更清晰。

第二，**CSS 体积更容易控制** 。

因为它生成的是**原子 CSS** 。项目越大，很多样式规则会被复用，CSS 体积不会随着组件数量线性爆炸。

第三，**类型安全** 。

这是**Tailwind** 比较弱的地方。`StyleX` 的样式、变量、主题都可以接入类型系统。对于设计系统来说，这很关键。比如颜色、间距、主题变量，不再是随便写字符串，而是可以被类型约束。

第四，**组合能力强** 。

你可以这样写：
```

stylex.props( styles.base, isActive && styles.active, disabled && styles.disabled )
```

条件样式、变体样式、外部传入样式，都可以组合，而且规则可预测。

第五，**更适合组件库** 。

如果你在做业务页面，`Tailwind` 很爽。但如果你在做一套长期维护的组件库，问题就不一样了。组件库需要默认样式，也需要外部覆盖；需要主题，也需要类型约束；需要局部样式，也需要跨项目复用。

这正是`StyleX` 擅长的场景。

## 写在最后

这几年，前端样式方案其实一直在两个方向之间摇摆。

一个方向是`Tailwind`：
```

直接、快速、工具类优先
```

另一个方向是`StyleX`：
```

组件化、类型安全、编译期优化
```

前者适合快速交付，后者适合长期工程。

所以我不觉得`StyleX` 会立刻取代`Tailwind`。

但它代表了一个很明确的趋势：

**CSS-in-JS 没死，只是进入了编译器时代。**

以前我们靠运行时解决样式问题，现在越来越多问题会被提前放到构建阶段解决。

这也是前端工具链这几年的大方向。

能静态分析的，就不要留到运行时。

能编译解决的，就不要交给浏览器硬扛。

而`StyleX`，就是这个趋势下最值得关注的样式方案之一。

  * **StyleX 官网** ：`https://stylexjs.com/`
  * **Astryx Design 官网** ：`https://astryx.atmeta.com/`


