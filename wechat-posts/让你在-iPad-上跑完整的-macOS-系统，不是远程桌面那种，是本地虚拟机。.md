# 让你在 iPad 上跑完整的 macOS 系统，不是远程桌面那种，是本地虚拟机。

**作者**: github淘金
**发布时间**: 2026-08-05 08:56
**原文链接**: https://mp.weixin.qq.com/s/nOdrv_0eiVgN5U69SzveIg

---

# VirtualMacOniPad

> 给 M1/M2 iPad Pro 和 M1 iPad Air 用的越狱工具，装完就能在 iPad 上开 macOS 虚拟机，原生跑 Xcode、Terminal 这些专业软件。

Github地址

https://github.com/nfzerox/VirtualMacOniPad

![](https://r2.jeanjan.kdns.fr/pictures/img-7152267901.png)

## 功能特性

  * 硬件级 CPU 虚拟化，不是纯软件模拟，所以日常用起来还算流畅
  * 支持显卡加速，图形性能跟 Mac 上的 UTM、VirtualBuddy 差不多一个水平
  * macOS 12 到 macOS 27 都能装，推荐 13 Ventura 到 15 Sequoia，新版 26/27 也能跑但可能有 bug
  * 不用 Magic Keyboard 也能玩，触屏点按配合虚拟键盘，就是操作麻烦点

## 怎么用：

机器得先越狱。iPadOS 16.0 到 16.3.1 的系统，用 Dopamine 配合 TrollInstallerX 搞定，越狱失败的话换别的 exploit 试试。然后在 Sileo 里加源 `https://nfzerox.github.io/cydia/`，搜 Virtual Mac 安装就行。装系统的时候选"稍后设置"跳过 Apple ID 登录，这功能不支持。

## 有个坑

16.4 之后苹果把 Hypervisor 从 iPadOS 内核里删了，所以新版系统用不了。项目方说加 15 的支持应该不难，欢迎有人去贡献代码。出问题了先去 GitHub 开 issue，附上报错和崩溃日志，有 Codex 或 Claude Code 的也可以连上 iPad 让 AI 直接调试。

  


