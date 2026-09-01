# 开源版 Figma 真来了：Penpot 本地部署，外网也能访问

**作者**: cpolar极点云
**发布时间**: 2026-07-05 15:05
**原文链接**: https://mp.weixin.qq.com/s/gfe3qWVHZBooWOR17tR-EQ

---

## 开源版 Figma 真来了：Penpot 本地部署，外网也能访问

![image-20260701185223745](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e201.png)

## 前言

提到设计协作工具，**Figma** 几乎已经成了很多人的默认选择。

浏览器打开就能画 UI、做原型、团队协作，设计师和开发之间的沟通也方便了很多。但对一些个人开发者、小团队，或者内部项目来说，Figma 也有一些绕不开的顾虑。

设计稿放在云端，**数据不在自己手里** ；团队成员多了以后，**账号和订阅成本** 也会变成长期支出。尤其是内部系统、客户项目、产品原型这类资料，很多时候还是希望能放在自己的环境里管理。

有没有一种工具，既能像 Figma 一样做 **UI 设计、原型和团队协作** ，又能 **自己部署** ，数据也放在自己手里？

**Penpot** 就是这样一个很值得关注的开源项目。它支持 UI 设计、交互原型、团队协作和设计系统管理，也支持 **自托管部署** ，可以搭建在自己的服务器、NAS 或本地环境中。

## 1 什么是Penpot？

![image-20260702134941534](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e202.png)

> 项目地址：https://github.com/penpot/penpot

**Penpot** 是一款面向设计师和开发者的 **开源 UI/UX 设计协作平台** 。简单理解，它有点像开源版 Figma，可以在浏览器里完成界面设计、原型制作、团队协作和设计交付等工作。

和传统设计工具不同，Penpot 从一开始就更强调 **设计与开发协作** 。它基于 Web 使用，设计过程中会尽量贴近 **SVG、CSS、HTML** 这些开放标准，开发者在检查设计稿时，可以更直接地看到可用于开发的样式和代码信息。官方也明确把它定位为连接设计与代码工作流的开源设计工具。

除了常规的 UI 设计和团队协作，Penpot 还有一个很值得关注的方向：**AI 工作流** 。官方已经提供了 **Penpot MCP Server** ，可以让 Codex、Cursor、Claude Code、VS Code 等支持 MCP 的 AI 工具连接到 Penpot，让 AI Agent 直接参与设计流程。

通过 MCP，AI 不只是“看设计稿”，还可以读取和操作 Penpot 文件结构，比如页面、图层、组件、样式、Design Tokens 等。也就是说，后续可以让 AI 帮忙生成页面、整理图层、创建组件、调整样式，甚至根据已有设计系统生成新的界面。

简单来说，Penpot 不只是一个开源设计工具，它更像是一个可以自建、可协作、还能接入 AI Agent 的设计工作台。

| 能力方向         | Penpot 可以做什么                                    |
|--------------|-------------------------------------------------|
| UI 设计        | 绘制页面、线框图、移动端界面和 Web 界面                          |
| 原型协作         | 制作交互原型，支持团队在线协作和设计交付                            |
| 设计系统         | 管理组件、样式、Design Tokens 和共享库                      |
| 自托管部署        | 可以部署到自己的服务器、NAS 或本地环境                           |
| 开放标准         | 基于 SVG、CSS、HTML 等 Web 标准，减少私有格式锁定               |
| MCP / AI 工作流 | 让 Codex、Cursor、Claude Code 等 AI Agent 读取和操作设计文件 |

## 2 先看效果：让 Codex 通过 MCP 生成 UI

现在 **Figma** 也已经支持 **MCP** ，可以让 AI 工具读取设计稿、辅助生成代码。不过从官方文档来看，Figma MCP 会受到 **套餐、席位和调用额度** 限制：普通 View / Collab 席位每月只有较低的调用额度，桌面版 MCP 也需要付费计划中的 Dev 或 Full seat。

相比之下，**Penpot MCP Server** 更适合自建和折腾型工作流。它可以连接 **Codex、Cursor、Claude Code、VS Code** 等支持 MCP 的 AI 工具，让 **AI Agent** 读取和操作 Penpot 里的 **页面、图层、组件、样式和 Design Tokens** 。

### 2.1 使用 Codex 调用 Penpot MCP

在正式部署之前，先看一下最终能做到什么效果，这里以制作一个【学生信息管理系统】的移动端H5的UI页面为例，首先需要开启**penpot** 的**MCP** 能力：

![image-20260702143316161](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e203.png)

接着，复制下面带token的mcp地址替换下面提示词中的mcp链接占位，然后将这段提示词发送给 Codex 或其他支持 MCP 的 AI Agent 工具即可：
```

我有一个本地 Penpot 实例，已经启用了 MCP。  
  
MCP 地址如下，请把它当作敏感 token，不要在回答中复述，也不要在日志、代码注释、最终回复中打印：  
  
【把你的 Penpot MCP 地址粘贴到这里】  
  
请连接这个 Penpot MCP，并在我当前打开的 Penpot 文件和当前页面里，设计一套“移动端 H5 学生信息管理系统”原型。  
  
要求：  
```

    1. 先调用 MCP 工具确认连接状态，读取 Penpot high_level_overview 和必要的 API 信息。  
    2. 使用 Penpot MCP 的 execute_code 直接在画布中创建设计稿，不要只给文字方案。  
    3. 设计 5 个移动端页面，尺寸 390 × 844：  
```
   - 首页 / 数据概览  
   - 学生列表  
   - 学生详情  
   - 新增或编辑学生  
   - 成绩统计  
```

    4. 所有页面内容必须使用中文，不要用英文替代。  
    5. 页面风格：清爽、现代、适合学校教务/班主任使用，不要做成营销落地页。  
    6. 每个页面都要包含真实业务信息，例如学生姓名、学号、班级、手机号、考勤状态、综合分、成绩趋势等。  
    7. 元素需要可编辑，尽量用 Penpot 原生形状和文本创建。  
    8. 注意中文字体渲染：先创建一个小的中文文本测试并导出/检查。如果中文不可见，不要改成英文，请改用 Penpot 当前环境可显示的中文字体或其他稳定方案，让中文在画布中真实可见。  
    9. 完成后请告诉我创建了哪些画板，并导出首页预览检查一次。

如下图：![image-20260702144112991](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e204.png)

此时可以看到打开的设计页面，目前还是空白的：![image-20260702144922469](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e205.png)

等待Codex设计，可以看到它已经连接上了MCP，并且还测试了一下：![image-20260702145556423](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e206.png)

回到设计页面，也可以看到它成功的创建了一个测试页面：![image-20260702145632985](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e207.png)

继续等待Codex，等待了20分钟左右，Codex提示已经完成了，如下图：![image-20260702151248153](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e208.png)

回到浏览器的设计页面查看：![image-20260702151359360](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e209.png)

可以看到，Codex已经完成了5个页面的设计，并且画的非常漂亮！换做**Figma** 来设计的话，在普通 View / Collab 席位下，应该已经受MCP的调用次数限制而停止了。

## 3 Windows 一键部署 Penpot

前面已经看到了 Penpot + MCP + Codex 的实际效果，接下来开始部署 Penpot。

在开始之前，需要先确认电脑已经安装并启动 **Docker** 。如果还没有安装 Docker，可以参考这篇教程先完成安装：

> Docker 安装教程：https://www.cpolar.com/blog/docker-installation-linux-windows-macos

### 3.1 使用Docker一键脚本部署

Penpot 官方支持 Docker Compose 部署，不过原始配置文件内容比较多，对于只想快速体验的用户来说，手动下载、修改配置、启动容器还是稍微有点麻烦。

为了简化部署过程，这里直接使用整理好的一键部署脚本。脚本会自动准备 Penpot 所需配置，并通过 Docker Compose 启动相关服务。

Docker安装完成启动后，电脑按【Win+X】键选择【终端（管理员）】打开 **PowerShell** ，执行下面命令：
```

irmhttps://gitee.com/jun-wan/script/raw/master/penpot_deploy/deploy-penpot.ps1|iex
```

输入回车后，会进入如下图：![image-20260702154659621](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e210.png)

选择数字【1】回车，然后按照提示进行自定义配置部署：![image-20260702155429473](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e211.png)

等待镜像拉取完成，即可看到部署成功提示：![image-20260702161710934](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e212.png)

在浏览器中访问9001端口的这个地址：![image-20260702161749380](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e213.png)

可以看到成功访问到了 **Penpot 的登录页面** ，说明本地 Penpot 服务已经启动成功。点击底部的创建账号，创建一个账号便可以进入工作台页面：![image-20260702162230495](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e214.png)

## 4 下载安装cpolar

到这里，Penpot 已经在本地部署完成了，浏览器访问 `localhost:9001` 就能打开。但这个地址只能在当前电脑上使用，别人无法直接通过互联网访问。

前面效果演示中使用的 `https://penpot.cpolar.top`，就是通过内网穿透工具 cpolar 将本地 `9001` 端口映射到公网后得到的访问地址。也就是说，Penpot 实际还是运行在本地 Docker 里，只是通过 cpolar 多了一条外网访问通道。

接下来就来安装 cpolar，并把本地的 Penpot 服务映射成一个公网地址。

### 4.1 什么是cpolar?

![image-20250910114418412](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e215.png)

**cpolar** 是一款内网穿透工具，可以将本地电脑、NAS、服务器中运行的 Web 服务映射到公网，让外部设备也能通过浏览器访问。

比如现在 Penpot 运行在本地的 `9001` 端口，正常情况下只能在当前电脑或局域网中打开。通过 cpolar 创建 HTTP 隧道后，就可以生成一个公网访问地址，在外网也能访问本地部署的 Penpot。

对于没有公网 IP、不想配置路由器端口转发，或者只是想快速临时分享本地服务的用户来说，cpolar 会比较方便。后面我们会用它把本地的 Penpot 服务映射出去，实现远程访问。

### 4.2 下载安装cpolar

打开cpolar官网的下载页面：https://www.cpolar.com/download点击【立即下载 64-bit】按钮,下载cpoalr的安装包:

![image-20250815171202537](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e216.png)

下载下来是一个压缩包，解压后执行目录中的应用程序，一路默认安装即可，安装完成后，打开cmd窗口输入如下命令确认安装:
```

cpolarversion
```

![image-20250815171446129](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e217.png)

出现如上版本即代表安装成功!

### 4.3 注册及登录cpolar web ui管理界面

官网链接：https://www.cpolar.com/

访问cpolar官网，点击`免费注册`按钮，进行账号注册：

![image-20250804085039567](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e218.png)

进入到如下的注册页面进行账号注册：![image-20260301193227057](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e219.png)注册完成后,在浏览器中输入如下地址访问 web ui管理界面:
```

http://127.0.0.1:9200
```

![image-20250815171734046](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e220.png)

输入刚才注册好的cpolar账号登录即可进入后台页面:

![image-20250815171846757](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e221.png)

## 5 使用cpolar穿透Penpot

刚才已经成功安装并登录了 cpolar，接下来就可以创建 HTTP 隧道，将本地运行在 `9001` 端口的 Penpot 映射到公网。

cpolar 这里可以有两种使用方式：

-**随机域名方式** ：创建后会自动生成一个临时公网地址，适合快速测试；-**固定域名方式** ：可以绑定固定二级子域名，适合长期访问和分享给团队成员使用。

下面分别演示这两种方式。

### 5.1 随机域名方式(免费方案)

随机域名方式更适合**临时测试或短期使用** 。使用该方式时，公网访问地址会在一段时间后**发生变化** ，通常不适合长期固定访问。不过它的优点是**配置简单、可以免费体验** 。如果后续需要长期访问 Penpot，或者希望团队成员使用同一个稳定地址，可以继续参考后面的 **固定域名方式** ，访问体验也会更稳定。

点击左侧菜单栏的【隧道管理】，展开进入【隧道列表】页面，页面下默认会有 2 个隧道：

  * remoteDesktop隧道，指向3389端口，tcp协议

  * website隧道，指向8080端口，http协议（http协议默认会生成2个公网地址，一个是http，另一个https，免去配置ssl证书的繁琐步骤）

![image-20250914174356363](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e222.png)

点击编辑【website】隧道或创建一条新的隧道，设置一个隧道名称（自定义即可）,协议选择【http】,本地地址填写Penpot的访问端口【9001】，地区这里选择的【China VIP】，最后点击更新：

![china_vip](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e223.png)

接着，点击左侧菜单栏的【状态】，进入【在线隧道列表】页面。这里可以看到两条名称为【penpot】的在线隧道，分别对应 http 和 https 协议:

![image-20260702171852368](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e224.png)

接着，回到PowerShell终端，重新执行一键部署管理脚本：
```

irm https://gitee.com/jun-wan/script/raw/master/penpot_deploy/deploy-penpot.ps1 | iex
```

回车后，选择数字【9】，进行设置穿透域名，如下图：![image-20260702172201409](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e225.png)

接着，将在线隧道列表显示的公网地址，复制粘贴到终端回车，进行重建容器应用该公网地址，这里以https为例：![image-20260702172421090](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e226.png)

提示完成后，在浏览器中打开刚才复制的公网地址（页面如果没出来，可以使用ctrl + f5强制刷新一下）：

![image-20260702172627319](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e227.png)

可以看到，通过 cpolar 生成的公网地址，已经能够正常打开 Penpot 登录页面。说明本地运行的 Penpot 服务已经成功映射到公网，后续在外部网络中也可以通过这个地址访问。

### 5.2 固定域名方式

通过前面的配置，我们已经可以使用随机公网地址访问 Penpot。不过随机域名更适合临时测试，地址可能会在一段时间后发生变化。如果后续需要**长期访问 Penpot** ，或者需要把地址分享给团队成员使用，建议配置**固定二级子域名** 。

固定域名配置完成后，访问地址会更加稳定，后续打开 Penpot 时就不需要频繁更换访问链接。

首先，进入 cpolar 官网后台的预留页面：
```

https://dashboard.cpolar.com/reserved
```

选择左侧菜单栏的【预留】，找到【保留二级子域名】区域，填写【地区、二级域名、描述】等信息，然后点击【保留】按钮：![image-20260702174008450](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e228.png)这里需要注意：

  * **地区** ：建议选择和前面创建隧道时一致的地区，例如 China VIP

  * **二级域名** ：填写想要使用的名称，例如 `penpot`

  * **描述** ：可以填写 `penpot`，方便后续识别

保留成功后，列表中会显示一条已保留的二级子域名记录。

> **注意：** 这里的二级域名是唯一的，每个账号可用的名称不同，请以自己实际保留成功的二级域名为准。

接着，接着，回到本地 cpolar Web UI 管理界面，点击左侧菜单栏的【隧道管理】，进入【隧道列表】页面，找到前面创建的 `penpot` 隧道，点击右侧【编辑】按钮:![image-20260702174237858](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e229.png)

将域名类型修改为【二级子域名】，并填写刚才在官网后台保留的二级子域名,其他配置保持和前面一致：

  * **协议** ：http

  * **本地地址** ：9001

  * **域名类型** ：二级子域名

  * **Sub Domain** ：填写刚才保留的二级域名，例如 `penpot`

  * **地区** ：选择和保留域名时一致的地区，例如 China VIP

配置完成后，点击【更新】按钮:![image-20260702174343525](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e230.png)

更新完成后，点击左侧菜单栏的【状态】，进入【在线隧道列表】页面。这里可以看到 `penpot` 隧道已经生成了固定的公网访问地址:![image-20260702174452547](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e231.png)

接着，回到 PowerShell 终端，再次重新执行 Penpot 一键部署管理脚本：
```

irmhttps://gitee.com/jun-wan/script/raw/master/penpot_deploy/deploy-penpot.ps1|iex
```

进入菜单后，选择数字【9】，重新设置 Penpot 的穿透域名为刚才固定的公网地址:

![image-20260702174654699](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e232.png)

回车后，脚本会自动重建 Penpot 容器，并应用新的公网访问地址。等待提示完成后，在浏览器中打开刚才配置的固定域名：

![image-20260702174724676](https://r2.jeanjan.kdns.fr/pictures/img-9f0035e233.png)

页面可以正常打开，说明固定域名方式已经配置完成。后续访问 Penpot 时，就可以直接使用这个固定的地址啦！

## 总结

通过这次部署，我们把 Penpot 跑在了本地环境中，并通过 cpolar 将本地 `9001` 端口映射到公网，实现了外网访问。这样既可以体验 Penpot 这类开源设计协作工具，也能把设计稿、原型和团队协作流程放在自己可控的环境里。

  * **自托管更灵活** ：Penpot 可以部署在本地电脑、NAS 或服务器中，适合个人开发者、小团队以及内部项目使用。

  * **协作能力完整** ：它支持 UI 设计、原型制作、团队协作、设计系统管理，也可以通过 MCP 接入 Codex、Cursor、Claude Code 等 AI 工具。

  * **远程访问更方便** ：配合 cpolar 后，即使没有公网 IP，也可以通过公网地址访问本地 Penpot，随机域名适合临时测试，固定域名更适合长期使用。

整体来看，Penpot 并不是简单的 “Figma 平替”，而是一个更适合自建和开放工作流的设计平台。对于希望掌握数据、降低工具成本，并尝试 AI Agent 参与设计流程的用户来说，Penpot + cpolar 是一个很值得尝试的组合。

感谢您阅读本文，有任何问题欢迎留言交流。

如需转载请注明出处！  

  


