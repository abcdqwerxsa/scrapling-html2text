# 无虚拟 DOM 版 React 发布！对决 Vue Vapor，谁才是未来前端框架？

**作者**: 前端开发爱好者
**发布时间**: 2026-08-13 08:33
**原文链接**: https://mp.weixin.qq.com/s/iEHIdOPQuzYFQJ74XQCIBg

---

前端框架的**性能战争** ，似乎又回来了。

过去几年，`React`、`Vue`、`Svelte`、`Solid` 都在尝试回答同一个问题：

**我们到底还需不需要 Virtual DOM？**

现在，一个很有意思的新框架出现了——**Octane** 。

![](https://r2.jeanjan.kdns.fr/pictures/img-a3a06ab301.jpeg)

如果非要用一句话介绍它，可以这么说：

> **它想做一个“没有 Virtual DOM 的 React”。**

` 函数组件`、`Hooks`、`Context`、`Suspense`、`Transition`，这些 **React** 开发者熟悉的东西，它基本都想保留。

但 **React** 身上那些让人又爱又恨的东西，比如：

  * `Virtual DOM`
  * `Rules of Hooks`
  * `useEffect` 依赖数组
  * `useMemo`
  * `useCallback`
  * 大量运行时 `diff`

**Octane** 则希望通过编译器统统解决掉。

那么问题来了：

**这个“无虚拟 DOM 版 React”，到底是什么来头？**

以及：

**如果 Octane 遇上 Vue Vapor，到底谁更强？**

##  React 最大的问题，可能已经不是 React API 了

先说一个很有意思的现象。

今天很多开发者吐槽 **React** ，吐槽的其实已经不是 `JSX`，也不是`函数组件`。

恰恰相反。

**React** 最成功的地方，就是它建立了一套非常有影响力的组件编程模型：
```

function Counter() {  
  const [count, setCount] = useState(0)  
  
  return (  
    <button onClick={() => setCount(count + 1)}>  
      Count: {count}  
    </button>  
  )  
}  

```

组件是函数。

状态写在组件里面。

**UI** 是状态的映射。

这套思路已经深入整个前端生态。

真正的问题是：

**为了维持这套编程模型，React 在运行时付出了多少代价？**

其中最典型的就是 `Virtual DOM`。

当 **state** 更新以后，**React** 通常需要：
```

state 更新  
↓  
组件重新执行  
↓  
生成新的 Virtual DOM  
↓  
和旧 Virtual DOM 比较  
↓  
找出变化  
↓  
更新真实 DOM  

```

这套机制的最大优点，是简单、通用。

**React** 不需要提前知道：

> 到底哪一个 DOM 节点依赖 `count`？

组件重新跑一次，再 `diff` 就行了。

但问题同样明显。

**如果编译器其实能够提前知道依赖关系呢？**

那为什么还要重新生成一棵 `Virtual DOM`？

这恰恰就是 **Octane** 想解决的问题。

## Octane：React 的写法，Solid/Svelte 的执行方式？

**Octane** 最有意思的地方，不是它创造了一个全新的组件模型。

反而是它选择：

**尽可能保留 React。**

比如一个 **Octane** 组件大致可以这样写：
```

import { useState, useEffect } from 'octane'  
  
export function Counter(props) @{  
  const [count, setCount] = useState(0)  
  
  if (!props.paused) {  
    useEffect(() => {  
      console.log('count:', count)  
    })  
  }  
  
  <button onClick={() => setCount(count + 1)}>  
    {'Count: ' + count}  
  </button>  
}  

```

**React** 开发者第一眼看上去基本没有什么学习成本。

但仔细看，你会发现两个非常“反 React”的地方。

第一：
```

if (!props.paused) {  
  useEffect(...)  
}  

```

**Hook 居然写在 if 里面。**

第二：
```

useEffect(() => {  
  console.log(count)  
})  

```

**依赖数组没了。**

如果把这段代码直接放进 **React** ，我们都知道会发生什么。

但 **Octane** 可以这么做。

原因就在于：

> **Octane 不需要靠 Hook 的执行顺序来识别状态。**

##  Rules of Hooks，终于可以消失了？

**React Hooks** 有一个几乎所有开发者都背过的规则：

> **Hooks** 不能写在条件语句里。

所以你不能这样：
```

if (enabled) {  
  useEffect(...)  
}  

```

为什么？

因为 **React** 需要依赖 **Hook** 的调用顺序来识别每一次调用对应哪个状态。

可以简单理解成：
```

第一次 useState → state 0  
第二次 useState → state 1  
第三次 useEffect → effect 2  

```

如果某一次 `render` 中少执行了一个 **Hook** ，顺序就乱了。

于是 **React** 才需要 `Rules of Hooks`。

这并不是因为：

> “条件 Hook 在理论上不合理。”

而是因为：

> **React 当前运行时识别 Hook 的方式决定了它不能这么写。**

**Octane** 换了一个思路。

既然有编译器，那编译器完全可以在编译阶段确定：
```

这里有一个 useState  
这里有一个 useEffect  
这个 effect 出现在这个条件分支  

```

于是：

**Hooks 不再需要依靠运行时调用顺序定位。**

` Rules of Hooks`，自然就可以消失。

这可能是 **Octane** 对 **React** 开发者最有吸引力的一点。

## 更重要的是：依赖数组也消失了

很多 **React** 开发者真正头疼的，可能还不是 `Rules of Hooks`。

而是：
```

useEffect(() => {  
  fetchUser(userId)  
}, [userId])  

```

为什么需要：
```

[userId]  

```

因为 **React** 本身不知道 `effect` 内部依赖了哪些变量。

于是只能让开发者告诉它：

> 当 `userId` 发生变化的时候，请重新执行。

问题是，一旦逻辑复杂起来：
```

useEffect(() => {  
  if (enabled) {  
    request(userId, token, config)  
  }  
}, [enabled, userId, token, config])  

```

依赖数组越来越长。

漏掉一个值，可能出现 stale closure。

放多一个对象，又可能让 effect 疯狂执行。

然后开发者继续开始：
```

useMemo(...)  
useCallback(...)  

```

最终一个本来很普通的组件，里面全是：
```

useEffect  
useMemo  
useCallback  
dependency array  
eslint-disable  

```

**Octane** 的思路则是：**既然编译器能看到代码，那为什么让人手写依赖？**

例如：
```

useEffect(() => {  
  console.log(count)  
})  

```

编译器已经看到了：
```

这个 effect 读取了 count  

```

那它就可以自动建立：
```

count → effect  

```

之间的依赖关系。

从这个角度看，**Octane** 做的事情，其实和近几年整个前端发展的趋势高度一致：

> **把人肉优化，交给编译器。**

##  真正的大招：Octane 不需要 Virtual DOM

这才是 **Octane** 最核心的部分。

传统 **React** 大致是：
```

状态变化  
↓  
组件执行  
↓  
Virtual DOM  
↓  
Diff  
↓  
DOM 更新  

```

而 **Octane** 希望在编译之后，直接变成类似：
```

状态变化  
↓  
定位对应更新点  
↓  
修改 DOM  

```

例如：
```

<div>{count}</div>  

```

经过编译器分析之后，它知道：
```

这个文本节点依赖 count  

```

于是当 `count` 更新时，没有必要重新构造整个组件的 `Virtual DOM`。

直接更新这个文本节点即可。

这就是所谓的：

**Fine-grained Update。**

也就是细粒度更新。

如果你用过 **Solid** ，大概马上就知道这是什么意思。

## 那它和 Vue Vapor 有什么区别？

两者目标其实非常接近：

> **都想通过编译器和细粒度更新，把 Virtual DOM 拿掉。**

但实现思路不同。

#### Vue Vapor：响应式系统本来就知道依赖

**Vue** 本身拥有：
```

ref  
reactive  
computed  
watch  

```

例如：
```

const count = ref(0)  

```

模板中使用 `count` 后，**Vue** 很容易建立：
```

count → DOM 节点  

```

所以 **Vapor** 更像是在 Vue 原有响应式系统上，**拆掉 Virtual DOM 这一层** 。

#### Octane：让编译器把 React 代码变成响应式程序

**React** 的 `useState` 并不是传统 Signal。

因此 **Octane** 要依赖编译器分析：
```

const [count, setCount] = useState(0)  
  
<div>{count}</div>  

```

然后推导出：
```

count → DOM 节点  

```

所以 **Octane** 做的事情更激进：

> **保留 React 的写法，但把运行机制改造成 Fine-grained Reactive。**

##  性能谁更强？

按照 **Octane** 官方公布的 `Benchmark`

![](https://r2.jeanjan.kdns.fr/pictures/img-a3a06ab302.jpeg)

整体几何平均结果大致是：

| 框架                      | 相对结果     |
|-------------------------|----------|
| **Octane TSRX**         | **1.0×** |
| **Vue Vapor**           | **1.2×** |
| **Solid 2**             | **1.7×** |
| **Svelte 5**            | **2.7×** |
| **React 19 + Compiler** | **4.1×** |

数值越低越好。

也就是说，在这套测试里：

> **Octane 和 Vue Vapor 基本处在同一档。**

不过官方 **Benchmark** 不能直接等同于真实业务性能。不同场景下，`Vue Vapor`、`Solid` 等框架都可能有更好的表现。

## Octane VS Vue Vapor，谁更有优势？

如果看架构天然程度，**Vue Vapor 更顺** 。

![](https://r2.jeanjan.kdns.fr/pictures/img-a3a06ab303.jpeg)

**Vue** 本身就是响应式框架，**Vapor** 只需要进一步减少运行时和 `Virtual DOM` 开销。

如果看迁移吸引力，**Octane 更有想象空间** 。

因为它瞄准的是庞大的 **React** 开发者：
```

React 写法  
+ 无 Rules of Hooks  
+ 无依赖数组  
+ 无 Virtual DOM  
+ Fine-grained 更新  

```

这套组合非常诱人。

但 **Octane** 当前最大的问题也很明显：

> **生态和成熟度远远无法与 Vue、React 相比。**

所以现阶段，**Vue Vapor** 更像是成熟生态的一次架构升级，而 **Octane** 更像是一场大胆的实验。

## 写在最后

**Octane** 和 **Vue Vapor** 其实共同说明了一件事：

**前端正在进入“后 Virtual DOM”时代。**

过去：
```

声明式 UI  
≈  
Virtual DOM  

```

现在越来越多框架开始证明：
```

声明式 UI  
→ 编译器  
→ 精确 DOM 更新  

```

同样可以成立。

所以未来前端框架的竞争重点，可能不再是：**React VS Vue。**

而是：

> **谁的编译器能做更多工作，谁的运行时就能做更少工作。**

从这个角度看，**Octane** 和 **Vue Vapor** 真正打响的，其实是一场新的 **Compiler War** 。

  * **Octane 官网** ：`https://octanejs.dev/`
  * **Github 地址** ：`https://github.com/octanejs/octane`

  


