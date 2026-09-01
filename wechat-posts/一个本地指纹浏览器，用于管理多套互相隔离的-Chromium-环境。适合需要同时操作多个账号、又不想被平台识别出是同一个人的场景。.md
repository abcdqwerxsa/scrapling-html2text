# 一个本地指纹浏览器，用于管理多套互相隔离的 Chromium 环境。适合需要同时操作多个账号、又不想被平台识别出是同一个人的场景。

**作者**: github淘金
**发布时间**: 2026-07-22 08:44
**原文链接**: https://mp.weixin.qq.com/s/B6bJjN0d5On_R-15nK79rA

---

# OpenBrowser

> 一款本地桌面指纹浏览器，主要用来管理多套互相隔离的 Chromium 环境。开发者把它做成一个工具箱，把 Profile 隔离、代理配置、浏览器指纹参数、扩展管理、窗口同步、本地 API、MCP 集成和本地 RPA 流程这些功能都塞了进去

Github地址

https://github.com/lyu0805/OpenBrowser

![](https://r2.jeanjan.kdns.fr/pictures/img-336a41fb01.png)![](https://r2.jeanjan.kdns.fr/pictures/img-336a41fb02.png)

## 功能特性

  * 环境隔离：每个 Profile 独立，Cookie、缓存、本地存储互不串门
  * 批量操作：分组、打标签、批量启停、调窗口大小
  * 代理绑定：HTTP/HTTPS/SOCKS 都能挂，还能测出口 IP
  * 指纹参数：平台、语言、时区、UA、Canvas、WebGL、WebRTC 这些都能改
  * 扩展管理：内置的、自己装的、本地导入的都能按环境加载
  * 窗口同步：基于 CDP 同步点击、滚动、输入、切标签页
  * 本地 RPA：打开页面、等待、点击、输入、截图之类的自动化流程
  * 本地 API / MCP：默认监听 127.0.0.1:50325
  * 独立内核：能下载独立的 Chromium 内核，也能指定本地路径
  * 备份：本地、WebDAV、GitHub、网盘都能备，但要自己手动开

## 支持的平台

| 平台      | 架构     | 状态 |
|---------|--------|----|
| Windows | x86_64 | 能用 |
| macOS   | x86_64 | 能用 |
| macOS   | arm64  | 能用 |

## 几个注意点

  * 本地 API 默认只绑回环地址，外网进不来
  * 设了 `OPENBROWSER_API_KEY` 之后，请求要带头
  * 浏览器起不来会写日志到用户数据目录的 `browser-startup.log`，在 `Browserapp/` 里执行 `npm run log:startup` 能直接看
  * 云备份只有你自己配置了才会联网，默认不动
  * 内核不是仓库里带的，打包时从 Wayfern 官方源拉；macOS x86_64 用的是源码里已含的 OpenBrowser 148 运行时

  


