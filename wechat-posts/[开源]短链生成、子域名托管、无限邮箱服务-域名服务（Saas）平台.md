# [开源]短链生成、子域名托管、无限邮箱服务 域名服务（Saas）平台

**作者**: 小君技术
**发布时间**: 2026-08-06 08:21
**原文链接**: https://mp.weixin.qq.com/s/9R2KOnpQd2Ow3CEEuT7xrA

---

  

# 一、开源项目简介

  

# WR.DO

  

生成短链接, 创建 DNS 记录, 管理临时邮箱

  

WR.DO 是一个集成短链生成、子域名托管、无限邮箱服务，以及开放API接口的一站式域名服务（Saas）平台，释放你的域名潜力。

  

# 二、开源协议

  

使用MIT开源协议

  

# 三、界面展示

  

# 截图预览

  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
|                                                                 |
| ![图片](https://r2.jeanjan.kdns.fr/pictures/img-778c14bc01.jpeg) |
|                                                                 |    |
| ![图片](https://r2.jeanjan.kdns.fr/pictures/img-778c14bc02.jpeg) |
|                                                                 |
|-----------------------------------------------------------------|----|
|                                                                 |
| ![图片](https://r2.jeanjan.kdns.fr/pictures/img-778c14bc03.jpeg) |
|                                                                 |    |
| ![图片](https://r2.jeanjan.kdns.fr/pictures/img-778c14bc04.jpeg) |
|                                                                 |
|                                                                 |
| ![图片](https://r2.jeanjan.kdns.fr/pictures/img-778c14bc05.jpeg) |
|                                                                 |    |
| ![图片](https://r2.jeanjan.kdns.fr/pictures/img-778c14bc06.jpeg) |
|                                                                 |

  

# 四、功能概述

  

# 功能

  * **短链生成**  
生成附有访问者统计信息的短链接 (支持密码保护, 支持调用 API)  

  * **临时邮箱**  
创建多个临时邮箱接收和发送邮件（支持调用 API）  

  * **多租户支持**  
无缝管理多个 DNS 记录  

  * **截图 API**  
访问截图 API、网站元数据抓取 API  

**权限管理** ：方便审核的管理员面板  

  * **安全可靠**  
基于 Cloudflare 强大的 DNS API  

**功能列表**

  

短链服务：

支持自定义短链  

支持生成自定义二维码  

支持密码保护链接  

支持设置过期时间  

支持访问统计（实时日志、地图等多维度数据分析）  

支持调用 API 创建短链  

临时邮箱服务：

支持创建自定义前缀邮箱  

支持过滤未读邮件列表  

可创建无限数量邮箱  

支持接收无限制邮件 （依赖 Cloudflare Email Worker）  

支持发送邮件（依赖 Resend）  

支持调用 API 创建邮箱  

支持调用 API 获取收件箱邮件  

子域名管理服务：

支持管理多 Cloudflare 账户下的多个域名的 DNS 记录  

支持创建多种 DNS 记录类型（CNAME、A、TXT 等）  

开放接口模块：

获取网站元数据 API  

获取网站截图 API  

生成网站二维码 API  

将网站转换为 Markdown、Text  

支持所有类型 API 调用统计日志  

支持生成用户 API Key，用于第三方调用开放接口  

管理员模块：

多维度图表展示网站状态  

域名服务配置（动态配置各项服务是否启用，包括短链、临时邮箱（收发邮件）、子域名管理）  

用户列表管理（设置权限、分配使用额度、禁用用户等）  

短链管理（管理所有用户创建的短链）  

邮箱管理（管理所有用户创建的临时邮箱）  

子域名管理（管理所有用户创建的子域名）  

# 五、技术选型

  

# 快速开始

  

查看开发者快速开始的详细文档。

  

# 要求

Vercel 账户用于部署应用  

至少一个在 Cloudflare 托管的 **域名**  

查看开发文档。

  

# Email worker

  

查看 email worker 文档用于邮件接收。

  

# 自部署教程

  

# 使用 Vercel 部署

  

记得填写必要的环境变量。

  

# 使用 Docker Compose 部署

  

在服务器中创建一个文件夹，进入该文件夹并新建docker-compose.yml文件，填写必要的环境变量，然后执行：

  
  

```

docker compose up -d
```

  
  

# 本地开发

  

将 .env.example 复制为 .env 并填写必要的环境变量。

  
  

```

git clone wr.do  
cd wr.do  
pnpm install  
  
# 在 localhost:3000 上运行  
pnpm dev
```

  
  

# 初始化数据库

  
  

```

pnpm postinstall  
pnpm db:push
```

  
  

# 管理员初始化

  

Follow https://localhost:3000/setup

  
  
![](https://r2.jeanjan.kdns.fr/pictures/img-778c14bc07.webp)

  


