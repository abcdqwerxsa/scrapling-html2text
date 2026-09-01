# Anime.js + Three.js 联手：前端 3D 动画王炸组合来了！

**作者**: 前端开发爱好者
**发布时间**: 2026-06-24 08:33
**原文链接**: https://mp.weixin.qq.com/s/G-vKOJOgauyaESAOJStDEQ

---

`Anime.js 4.5` \+ `Three.js`，前端 **3D** 动画王炸组合来了！

**Anime.js 4.5** 重磅更新：官方直接引入了 `Three.js adapter` 。

![](https://r2.jeanjan.kdns.fr/pictures/img-abe7e3db01.png)

也就是说，`Anime.js` 不再只是做 DOM、SVG、普通 JS 对象动画，它开始真正进入 `Three.js` 这种 3D 场景了。

![](https://r2.jeanjan.kdns.fr/pictures/img-abe7e3db02.png)

官方文档里已经新增了一个 `Adapters` 分类，下面第一个就是 `Three.js`，而且标了一个醒目的 `NEW`。

这次更新的重点可以浓缩成一句话：

> **让 Three.js 动画写起来，更像前端熟悉的 CSS transform。**

##  Three.js 动画，为什么一直有点麻烦？

如果你写过 `Three.js`，应该知道它本身并不缺动画能力。

你可以改 `mesh.position`，可以改 `mesh.rotation`，可以改 `mesh.scale`，也可以改材质、灯光、相机、Shader uniforms。

问题是：**这些属性都太分散了。**

比如一个普通的 3D 对象动画，可能要同时操作：
```

mesh.position.x  
mesh.position.y  
mesh.rotation.x  
mesh.rotation.y  
mesh.scale  
mesh.material.opacity  
mesh.material.color  
uniforms.uTime.value  

```

写 Demo 还好，一旦进入真实项目，交互、时间轴、相机、材质、Shader、实例化网格一起上，代码很容易变成一团。

以前你可能要这样写：
```

createTimeline()  
  .add(mesh.position, {  
    x: 100,  
    y: 50,  
  }, 0)  
  .add(mesh.rotation, {  
    x: utils.degToRad(30),  
    y: utils.degToRad(60),  
  }, 0)  
  .add(mesh.material, {  
    opacity: 0.5,  
  }, 0);  

```

位置是位置，旋转是旋转，材质是材质，角度还要自己转弧度。

但在 `Anime.js 4.5` 里，引入 `Three.js adapter` 之后，可以直接这样写：
```

import { animate } from'animejs';  
import'animejs/adapters/three';  
  
animate(mesh, {  
x: 100,  
y: 50,  
rotateX: 30,  
rotateY: 60,  
opacity: 0.5,  
duration: 500,  
ease: 'inOutSine',  
});  

```

这就是这次更新最爽的地方。

`Anime.js` 会帮你把 `Three.js` 里那些嵌套属性，直接映射成更直观的动画参数。

比如：
```

x / y / z        -> position  
rotateX/Y/Z     -> rotation  
scale           -> scale  
opacity         -> material.opacity  
color           -> material.color  

```

你不需要一直在 `mesh.position`、`mesh.rotation`、`mesh.material` 之间切来切去，也不需要为了旋转手动写一堆 `degToRad()`。

## 像写 CSS transform 一样写 3D 动画

这次官方文档里专门给了一个 `Extended transforms` 案例。

它的核心就是：**把 CSS transform 的写法搬进 Three.js。**

以前你写网页动画，可能是这样：
```

transform: translateX(100px) rotateY(45deg) scale(1.2);  

```

现在写 `Three.js` 也可以接近这种感觉：
```

animate(mesh, {  
  x: 100,  
  rotateY: 360,  
  scale: 1.5,  
  skewX: 15,  
  transformOrigin: '0 1 0',  
});  

```

这里最关键的是，`Anime.js 4.5` 不只是支持普通的 `position` 和 `rotation`，还新增了更接近 CSS 体系的变换能力，比如：

  * `x / y / z`
  * `rotateX / rotateY / rotateZ`
  * `scale`
  * `skewX / skewY / skewZ`
  * `transformOrigin`

这对做 3D Hero、官网动效、产品展示页、WebGL 创意交互的人来说非常实用。

因为很多时候，我们不是不会写 `Three.js`，而是不想为了一个简单动效，写一堆底层对象操作。

现在 `Anime.js` 把它统一成了前端更熟悉的 API。

## 材质和 Uniform 动画也变简单了

这次还有一个非常重要的变化：**材质属性动画被简化了。**

以前你想改材质颜色，可能要操作 `material.color`；想改自发光颜色，要操作 `material.emissive`；想改 Shader 里的参数，还要去找 `uniforms.xxx.value`。

现在可以直接这样写：
```

animate(material, {  
  color: '#ff4fd8',  
  emissive: '#00ffff',  
  metalness: 1,  
  roughness: 0.2,  
});  

```

如果是自定义 Shader 里的 uniforms，也可以直接按名字传：
```

animate(material, {  
  uTime: 1,  
  uOffsetY: 0.5,  
});  

```

这对 `Three.js` 项目非常关键。

因为很多 3D 页面真正高级的地方，不只是模型在动，而是材质在动、颜色在动、光效在动、Shader 参数在动。

过去这些东西写起来非常零散，现在 `Anime.js 4.5` 直接把它们收口到同一个动画系统里。

而且颜色也更友好了，直接传 `RGB` / `HEX` 字符串即可，不需要自己手动处理颜色对象。

## InstancedMesh 也能像普通网格一样动了

这次官方还专门给了 `Instanced meshes` 案例。

这是非常硬核的一点。

在 `Three.js` 里，`InstancedMesh` 通常用于大量重复对象的高性能渲染，比如粒子矩阵、卡片墙、立方体阵列、产品队列、3D 数据点等。

性能是上去了，但问题也很明显：**实例化网格里的每个实例，并不像普通 mesh 那样好控制。**

` Anime.js 4.5` 新增了相关支持，可以通过 `getInstances()` 拿到每个实例的 proxy，然后像控制普通对象一样控制它们：
```

import { animate, stagger } from 'animejs';  
import { getInstances } from 'animejs/adapters/three';  
  
const instances = getInstances(mesh);  
  
animate(instances, {  
  x: 100,  
  scale: 2,  
  delay: stagger(20),  
});  

```

这意味着什么？

意味着你可以把一整个 `InstancedMesh` 里的对象，当成一组普通动画目标来处理。

比如做一个 3D 方块矩阵，每个方块依次弹出；做一组 3D 产品卡片，从中心向外扩散；做粒子波浪、空间队列、动态数据墙，都可以直接配合 `stagger()` 做。

这比自己去维护 instance matrix、索引、延迟、颜色更新要舒服太多了。

## 3D stagger：空间交错动画来了

`Anime.js` 本来就有很好用的 `stagger()`，可以做列表动画、网格动画、延迟扩散动画。

这次 `4.5` 把它升级到了 3D 场景。

简单说，过去你可能主要在二维平面里做 stagger，比如横向列表、纵向列表、二维网格。

现在它开始支持 3D 布局了。

比如：
```

animate(instances, {  
  y: 50,  
  delay: stagger(30, {  
    grid: [10, 10, 10],  
    from: 'center',  
  }),  
});  

```

这意味着 `stagger()` 不再只是网页列表动画工具，而是可以直接服务于 3D 空间动画。

更有意思的是，这次还新增了 `jitter` 和 `seed`。

`jitter` 可以给交错动画增加随机扰动，让动画不那么机械；`seed` 可以让随机结果可复现，避免每次刷新页面效果都完全不一样。

也就是说，你可以做出那种既自然、又可控的 3D 空间扩散效果。

## 这次更新真正改变了什么？

很多人看到 `Anime.js 4.5` 支持 `Three.js`，第一反应可能是：
```

哦，多支持了一个库。  

```

但这次更新其实不只是“多支持一个库”。

它真正做的是：**把 Three.js 里分散、嵌套、偏底层的动画目标，统一包装成了一个更前端化的动画 API。**

以前是：
```

Three.js 负责 3D  
动画逻辑你自己拼  

```

现在更像是：
```

Three.js 负责渲染世界  
Anime.js 负责驱动世界  

```

`Object properties` 解决的是嵌套属性太深的问题。

`Extended transforms` 解决的是 3D 变换写法不够直观的问题。

`Materials & uniforms` 解决的是材质和 Shader 参数动画太分散的问题。

`Instanced meshes` 解决的是大量实例对象不好批量动画的问题。

`3D stagger` 解决的是空间阵列动画不好编排的问题。

这几个能力叠在一起，才是 `Anime.js 4.5` 真正有意思的地方。

它不是替代 `Three.js`，也不是让你不学 `Three.js`。

它更像是在 `Three.js` 之上补了一层非常顺手的动画控制层。

## 前端为什么应该关注它？

这几年，前端页面越来越卷。

普通 landing page 已经不够了，越来越多产品官网开始用 3D Hero、WebGL 展示、交互式产品模型、空间卡片、粒子动效、Shader 背景。

但现实是，大部分前端并不是专业图形工程师。

大家真正需要的不是从零写一套 3D 引擎，而是能在合适的场景里，把 `Three.js` 用得更快、更稳、更好维护。

`Anime.js 4.5` 的价值就在这里。

它没有把事情复杂化，反而是把很多常见的 3D 动画操作简化了：
```

少写嵌套属性  
少写角度转换  
少写材质胶水代码  
少写实例化网格控制逻辑  
少写 stagger 计算逻辑  

```

官方说 3D 动画代码最多可以减少 50%，这个数字其实并不夸张。

因为在真实项目里，最耗代码量的往往不是动画本身，而是各种对象映射、状态同步和属性更新。

这次 `Anime.js 4.5` 就是直接砍掉了大量胶水代码。

## 写在最后

`Anime.js 4.5` 是一个很值得关注的版本。

它把 `Three.js` 动画从原来偏底层、偏分散的写法，往前端更熟悉的 `animate()`、`timeline`、`stagger()` 体系里拉了一大步。

对于做官网动效、3D 产品展示、WebGL 创意页面、互动可视化的前端来说，这次更新非常实用。

一句话总结：

**Anime.js 4.5 不是让你少学 Three.js，而是让你少写一半 Three.js 动画胶水代码。**

  * **Anime.js 4.5 相关信息** ：`https://github.com/juliangarnier/anime/releases/tag/v4.5.0`
  * **官网** ：`https://animejs.com/`


