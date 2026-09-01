# Electron、Tauri，该让位了！Vercel 造了个 6MB 原生框架！

**作者**: 前端开发爱好者
**发布时间**: 2026-07-10 08:33
**原文链接**: https://mp.weixin.qq.com/s/Y2Vp9sgIAmiqG_pegXoRWQ

---

前端开发桌面应用，一直都在做一道选择题。

想要开发简单、生态成熟，选 `Electron`。代价是应用里直接塞进一套 `Chromium + Node.js`，安装包、内存和启动速度都很难真正轻下来。

![](https://r2.jeanjan.kdns.fr/pictures/img-416380ac01.jpeg)

想要体积更小、性能更好，选 `Tauri`。它不再捆绑完整的 `Chromium`，改用系统自带的 `WebView`，但本质上依然是：
```

HTML + CSS + JavaScript  
↓  
系统 WebView  
↓  
Rust 原生能力  

```

现在，`Vercel Labs` 又给出了第三个答案。

项目叫 **Native SDK** 。

![](https://r2.jeanjan.kdns.fr/pictures/img-416380ac02.jpeg)

它直接绕开浏览器、`WebView` 和 `JavaScript` 引擎，用一套类似前端模板的 `.native` 语法写界面，再用 `Zig` 处理状态和业务逻辑，最终由自研渲染引擎，把像素直接画进系统窗口。

官方给出的数据也很夸张：
```

完整应用：小于 6 MB  
启动到首帧：约 100 ms  
内置浏览器：0  
JavaScript 引擎：0  
运行时解释器：0  

```

**Vercel Labs 这次，真把桌面应用的桌子掀了。**

##  Electron 为什么越来越重？

`Electron` 最大的优势，前端开发者都懂。

`Vue`、`React`、`Svelte` 随便选，`HTML`、`CSS`、`JavaScript` 直接写。浏览器里能跑的东西，基本都能搬进桌面应用。

它的架构也非常直接：
```

前端页面  
↓  
Chromium  
↓  
Node.js  
↓  
Windows / macOS / Linux  

```

这也是 `VS Code`、`Discord`、`Slack` 选择它的原因：

**开发效率高、平台差异小、Web 生态完整。**

但问题同样来自这套架构。

每个应用都要带上一套浏览器运行环境。即使你只是做一个简单的 `Markdown` 编辑器、文件工具或者状态栏应用，也需要背着 `Chromium` 和 `Node.js` 一起启动。

应用越来越大，内存占用越来越高，启动速度也很难真正做到原生级别。

简单来说，`Electron` 最大的优势是浏览器，最大的负担同样也是浏览器。

## Tauri 已经很轻，但还没有离开 WebView

`Tauri` 的思路聪明很多。

它没有把完整的 `Chromium` 打进安装包，而是直接调用操作系统提供的 `WebView`：
```

Vue / React / Svelte  
↓  
HTML + CSS + JavaScript  
↓  
系统 WebView  
↓  
Rust  

```

所以，`Tauri` 应用通常比 `Electron` 小很多，后端能力也可以交给 `Rust`，安全性和性能都有明显提升。

对于现有前端项目来说，迁移成本也比较低。只要最终能够编译成 `HTML`、`CSS` 和 `JavaScript`，基本都可以塞进 `Tauri`。

但它依然绕不开 `WebView`。

Windows 主要使用 `WebView2`，底层基于 `Edge Chromium`；macOS 使用 `WKWebView`；Linux 则依赖 `WebKitGTK`。

不同平台的浏览器版本、渲染结果和能力支持，仍然可能存在差异。

所以，`Tauri` 解决了**捆绑完整浏览器太重** 的问题，却没有彻底离开浏览器渲染。

**Native SDK 更激进。**

##  Native SDK：界面直接编译进应用

`Native SDK` 默认使用两种文件：
```

src/app.native  
src/main.zig  

```

`.native` 负责界面：
```

<column gap="12" padding="16">  
  <row gap="8" main="center" cross="center" grow="1">  
    <button variant="secondary" on-press="decrement">-</button>  
    <text>{count}</text>  
    <button variant="primary" on-press="increment">+</button>  
  </row>  
  
  <status-bar>count: {count}</status-bar>  
</column>  

```

看起来是不是很熟悉？

有组件、有属性、有事件、有数据绑定，整体写法非常接近 `HTML` 和现代前端框架的模板语法。

但它不会生成 `DOM`，也不会交给浏览器执行。

构建时，`.native` 界面会直接编译进可执行文件，由 `Native SDK` 自己的引擎完成布局、绘制和事件处理。

发布后的应用不需要携带：

  * 浏览器
  * `WebView`
  * 模板解析器
  * 脚本解释器
  * `JavaScript` 引擎

业务逻辑则写在 `Zig` 中：
```

pub const Msg = union(enum) {  
    increment,  
    decrement,  
    reset,  
};  
  
pub const Model = struct {  
    count: i64 = 0,  
};  
  
pub fn update(model: *Model, msg: Msg) void {  
    switch (msg) {  
        .increment => model.count += 1,  
        .decrement => model.count -= 1,  
        .reset => model.count = 0,  
    }  
}  

```

整个状态模型很简单：
```

用户操作  
↓  
发送 Msg  
↓  
update 修改 Model  
↓  
重新计算界面  

```

熟悉 `Redux`、`Elm`、`Pinia` 或者单向数据流的前端开发者，基本一眼就能理解。

界面只能读取状态和发送消息，不能在不同组件里随意修改数据。所有状态变化都集中在 `update` 中，调试、测试和 `AI` 生成都会更加稳定。

## 6MB、100ms，优势有多明显？

`Native SDK` 官方展示的多个完整应用，发布二进制都没有超过 `6 MB`：
```

Calculator：3.6 MB  
Markdown Viewer：3.5 MB  
Notes：3.5 MB  
Soundboard：5.7 MB  
System Monitor：3.7 MB  

```

在 `macOS ARM64` 环境下，这些示例从进程启动到第一帧显示，温启动时间约为 `71–131 ms`。

一个完整的 `Markdown` 编辑器示例，二进制只有 **3.4 MB** 。

原因很直接：
```

没有 Chromium  
没有 Node.js  
没有系统 WebView  
没有 JavaScript 引擎  
没有运行时模板解释器  

```

发布产物主要就是：
```

你的业务逻辑  
+  
Native SDK 渲染引擎  
+  
系统原生框架  

```

对于文件工具、桌面客户端、效率工具、`Markdown` 编辑器、数据库管理器、系统监控、内部工作台这类应用，这种体积和启动速度确实很有吸引力。

当然，这些数据来自项目方在指定设备和示例应用上的测试，不能直接得出“比 `Electron` 快几十倍”的结论。

两者提供的运行环境、浏览器能力和生态规模，本身就不在一个量级。

但有一点可以确定：

**当应用不再携带浏览器运行时，体积和启动速度自然会轻很多。**

##  Electron、Tauri、Native SDK 怎么选？

三套方案的技术路线已经非常清楚：

| 方案           | UI 技术             | 运行环境                 | 最大优势         | 主要代价                 |
|--------------|-------------------|----------------------|--------------|----------------------|
| `Electron`   | `HTML / CSS / JS` | `Chromium + Node.js` | 生态成熟，兼容性强    | 包体和资源占用较高            |
| `Tauri`      | `HTML / CSS / JS` | 系统 `WebView + Rust`  | 体积小，可复用前端项目  | 仍受 `WebView` 和平台差异影响 |
| `Native SDK` | `.native + Zig`   | 自研原生渲染引擎             | 无浏览器、体积小、启动快 | 生态早期，需要学习 `Zig`      |

`Electron` 依然适合复杂 Web 产品迁移，以及高度依赖浏览器生态的应用。

`Tauri` 适合希望继续使用 `Vue`、`React`，同时降低安装包和资源占用的团队。

`Native SDK` 瞄准的是另一类项目：

> **既想保留声明式 UI 的开发效率，又想真正摆脱浏览器运行时。**

它没有要求开发者回到繁琐的 `AppKit`、`Win32` 或 `GTK`，也没有继续把界面塞进 `WebView`，而是在两者之间重新造了一层。

## 前端开发者怎么快速上手？

安装非常简单，直接使用 `npm`：
```

npm install -g @native-sdk/cli  

```

创建项目：
```

native init my_app  
cd my_app  
native dev  

```

执行完成后，一个真实的系统窗口就会打开。

项目默认结构也很干净：
```

src/app.native   # 界面、布局、绑定、事件  
src/main.zig     # 状态和业务逻辑  
src/tests.zig    # UI 测试  
app.zon          # 应用配置、权限、窗口、打包信息  
assets/icon.png  # 应用图标  

```

开发过程中修改 `src/app.native`，窗口会自动更新，并尽量保留当前状态。

代码写错时，旧界面不会直接崩掉，还会返回具体的文件、行号和列号。

检查项目：
```

native check  

```

运行测试：
```

native test  

```

构建发布版本：
```

native build  

```

打包应用：
```

native package --target macos  
native package --target windows  
native package --target linux  

```

`CLI` 还会处理 `SDK` 路径和匹配版本的 `Zig` 工具链。

开发者不需要上来就维护复杂的 `build.zig`。项目真的需要自定义构建时，再通过 `native eject` 接管完整构建文件。

对于前端开发者来说，这套体验非常熟悉：
```

安装 CLI  
↓  
初始化项目  
↓  
启动开发服务器  
↓  
修改界面  
↓  
自动更新  
↓  
构建打包  

```

只是这一次，最终跑起来的已经不是网页。

## 五个平台，一套运行模型

`Native SDK` 当前已经覆盖：
```

macOS  
Windows  
Linux  
iOS  
Android  

```

![](https://r2.jeanjan.kdns.fr/pictures/img-416380ac03.jpeg)

桌面端是目前最成熟的部分。

### macOS

`macOS` 是当前支持最完整的平台，使用 `Metal` 呈现画面，同时接入系统滚动效果、菜单、托盘、弹窗和输入法。

### Windows 和 Linux

`Windows` 和 `Linux` 已经可以运行、测试和打包完整应用，不过当前主要使用 `CPU` 软件渲染，`GPU` 渲染后端仍在完善。

其中，`Linux` 暂时没有系统托盘支持，Windows 和 Linux 的部分系统能力也没有 macOS 完整。

### iOS 和 Android

移动端同样已经打通构建链路：
```

native dev --target ios  
native dev --target android  
  
native package --target ios  
native package --target android  

```

`iOS` 可以生成完整的 `Xcode` 工程，`Android` 可以生成完整宿主工程和调试 `APK`。

开发者不需要在项目里额外维护 `Swift`、`Kotlin` 或 `Java` 宿主代码。

但需要注意，`iOS` 和 `Android` 目前仍是实验性支持，主要在模拟器环境中验证，工具链、`API`、`GPU` 渲染和真机工作流都还在继续完善。

所以，现在用它做桌面工具已经很有讨论价值，直接拿去替换成熟的 `Flutter` 或 `React Native`，还太早。

## 它甚至是给 AI Agent 准备的

`Native SDK` 最特别的地方，可能还不是 **6 MB** 。

它直接把 `AI` 自动化能力做进了运行时。

`Agent` 可以读取正在运行的应用界面，查看无障碍树，查找按钮，输入文本，点击组件，验证状态，录制操作，并生成确定性的截图。
```

native automate wait  
native automate snapshot  
native automate screenshot  

```

项目还提供官方 `Agent Skills`：
```

npx skills add vercel-labs/native  

```

安装之后，`Claude Code`、`Codex` 等 `Agent` 可以获得与当前 `Native SDK` 版本匹配的开发说明。

`Agent` 写完界面后，还能直接启动应用、操作窗口、验证结果，再回头修改代码。

这套闭环很关键：
```

AI 生成界面  
↓  
编译运行  
↓  
读取真实窗口  
↓  
点击和测试  
↓  
发现问题  
↓  
自动修改  

```

以前，`AI` 写桌面应用，往往只能保证代码“看起来能跑”。

**Native SDK 想让 Agent 真正看到自己做出来的应用。**

它甚至可以通过组件来源信息，定位某个按钮来自哪个 `.native` 文件、哪一行代码，再自动完成修改。

这才是真正面向 `AI Agent` 的应用开发链路。

## 前端桌面开发，终于出现了第三条路

过去做桌面应用，前端开发者的选择并不多。

要么接受 `Electron` 的体积和资源占用，换取成熟生态与极低的上手成本；要么使用 `Tauri`，保留 Web 技术栈，再通过系统 `WebView` 和 `Rust` 换取更轻的应用。

`Native SDK` 选择了一条更激进的路线：
```

保留声明式 UI  
保留组件化开发  
保留数据绑定  
保留热更新  
保留前端熟悉的开发体验  
  
然后，删掉浏览器。  

```

它目前仍处于 `pre-1.0`，`API` 会继续变化，生态也远远无法和 `Electron`、`Tauri` 相比。

Windows、Linux 和移动端的渲染能力，同样需要继续完善。

但这个方向已经足够有意思。

**一个不到 6 MB、约 100 ms 启动、支持五个平台，还能让 AI Agent 直接操作和测试的原生应用框架。**

这一次，`Electron` 和 `Tauri` 的对手，真的来了。

  * **Native SDK 官网** ：`https://native-sdk.dev/`


