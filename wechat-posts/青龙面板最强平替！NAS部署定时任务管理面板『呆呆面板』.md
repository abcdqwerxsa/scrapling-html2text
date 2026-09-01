# 青龙面板最强平替！NAS部署定时任务管理面板『呆呆面板』

**作者**: Stark324
**发布时间**: 2026-08-06 20:31
**原文链接**: https://mp.weixin.qq.com/s/YU09CzSqm2H7ZDvcz3Mvaw

---

# 青龙面板最强平替！NAS部署定时任务管理面板『呆呆面板』

哈喽小伙伴们好，我是Stark-C~

关于青龙面板不用我多介绍，懂得都懂，不懂的不管是搜索还是问AI也会懂...

我也算是青龙面板的老用户了，不过因为众所周知的原因，青龙面板在年初被爆出漏洞被各大NAS应用商店紧急下架后，我也将它卸载了，自此之后再也没有使用。

这期间我也有意无意找个替代品，但一直没等到和青龙面板一样兼顾“脚本生态 + 定时任务 + 面板管理”一体化的定时任务管理面板。

直到最近，我终于遇到一个让我眼前一亮的选择：它不仅拥有青龙面板的核心功能，而且还比青龙面板更加轻量高效！最主要的是，它在NAS上部署起来也非常方便，非常值得大家体验。

PS：本文主要是教大家怎么在NAS上跑起来，因为项目的特殊性，它的用法和脚本相关这里就不提供了，大家可以直接搜索“青龙面板”的使用教程，基本上就能快速上手了（脚本也是一样找~）。

## 关于呆呆面板

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1301.png)

🔺呆呆面板(Daidai Panel)作为一款定时任务管理平台，在开发的时候其实是参考了青龙面板和白虎面板的设计理念，但在架构上做了彻底的轻量化重构：既保留了前辈们的脚本管理、环境变量、定时任务这些核心能力，同时又优化了整个运行流程和交互体验，让其更加轻量和现代。

项目Github地址：https://github.com/linzixuanzz/daidai-panel

（项目发布的时间不长，知道的人还不多，大家多多Star支持开发者）

**项目功能特性（引自官网）：**

  * 定时任务 — Cron 表达式调度，支持重试、超时、定时停止、任务依赖、前后置钩子
  * 脚本管理 — 在线代码编辑器，支持 Python、Node.js（含 ）、Shell、TypeScript、Go，拖拽移动文件.mjs
  * 执行日志 — SSE 实时日志流，历史日志查看与自动清理
  * 环境变量 — 分组管理、拖拽排序、批量导入导出（兼容青龙格式）
  * 订阅管理 — 自动从 Git 仓库拉取脚本，支持定期同步
  * 依赖管理 — 可视化安装/卸载 Python (pip) 和 Node.js (npm) 依赖
  * 通知推送 — Bark、Telegram、Server酱、企业微信、钉钉、飞书等 18 种渠道
  * 开放 API — App Key / App Secret 认证，支持第三方系统对接
  * 系统安全 — 双因素认证 (2FA)、IP 白名单、登录日志、多设备会话管理
  * 数据备份 — 一键备份与恢复，支持每天/每周/每月定时备份
  * 系统监控 — 实时 CPU / 内存 / 磁盘监控，任务执行趋势统计

## 呆呆面板部署

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1302.png)

🔺此次部署以极空间NAS为例，打开文件管理器，在Docker目录下新建一个“daidai-panel”的文件夹。

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1303.png)

🔺接着点击极空间NAS的“Docker”应用，点击【Compose】 > 【新增项目】。

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1304.png)

🔺在“创建项目”页面自定义项目名称，“存储位置”需要手动选择我们前面新建的“daidai-panel”文件夹，在方框中输入以下 Docker Compose 配置信息:
```

services:  
  daidai-panel:  
    image: linzixuanzz/daidai-panel:latest  
    container_name: daidai-panel  
    restart: unless-stopped  
    ports:  
      - "5700:5700"     # 项目打开端口，冒号前面请勿冲突  
    volumes:  
      - ./Dumb-Panel:/app/Dumb-Panel     
    environment:  
      - TZ=Asia/Shanghai  
      - CONTAINER_NAME=daidai-panel  
      - IMAGE_NAME=linzixuanzz/daidai-panel:latest  
      - PANEL_UPDATE_MANAGER=watchtower  
    labels:  
      - com.centurylinklabs.watchtower.enable=true  
  
  watchtower:  
    image: nickfedor/watchtower:latest  
    container_name: daidai-watchtower  
    restart: unless-stopped  
    volumes:  
      - /var/run/docker.sock:/var/run/docker.sock  
    labels:  
      - com.centurylinklabs.watchtower.enable=false  
    command:  
      - --label-enable  
      - --cleanup  
      - --interval  
      - "3600"  
  

```

以上代码需要修改的地方就看我给到的中文注释，其它的直接保持默认即可。镜像的拉取需要自行解决网络问题，粘贴到自己的NAS这边之前建议使用AI工具优化一下，以防止格式问题造成的部署失败。

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1305.png)

🔺部署好的项目会显示“正常”，就说明没问题，可以使用了。

## 呆呆面板体验

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1306.png)

🔺项目打开没啥不一样的，浏览器输入【IP:端口号】，或者直接使用极空间自己的的远程访问就可以了。首次使用需要自己随意设置一个管理员账号和密码。

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1307.png)

🔺熟悉的面板又回来了，但是个人觉得比青龙更加现代和直观。并且操作上几乎也和青龙面板一致，之前用过青龙面板的可以在这边直接上手。

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1308.png)

🔺在定时任务的创建上，呆呆面板也是直接支持标准 Cron 表达式调度，这个对于专业的开发者来说很是重要。另外它还有很多方便的快捷功能，比如说时间规则的快速选择、任务重试、前后置钩子等功能。

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1309.png)

🔺环境变量方面它支持安全存储敏感配置、变量值脱敏显示，以及任务执行时自动注入，同时它还支持批量导入导出并兼容青龙格式。

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1310.png)

🔺脚本文件管理方面它支持在线代码编辑器，支持创建、重命名、删除文件等实用功能，并且在文件操作层做了进一步优化，比如说支持在线编辑、语法高亮、自动保存等，让用户脚本开发和调试都能在面板内完成。

![](https://r2.jeanjan.kdns.fr/pictures/img-b35cdb1311.png)

🔺还有通知方面，它直接支持Bark、Server 酱、企业微信、钉钉、飞书等多达18 种消息推送渠道，可以为用户实时推送任务执行结果、系统事件告警等信息。

## 最后

总的来说，今天分享的这个项目还是非常强大的，并且它的稳定性也不错，至少在我使用的这一个星期内，它都一直保持着正常运行的状态。

它不仅可以完美的平替青龙面板，并且在整体体验上甚至比青龙面板还要好，尤其是在NAS上部署的资源占用方面，它确实比青龙面板要轻量很多，喜欢的小伙伴可以试试~ 好了，以上就是今天给大家分享的内容，我是爱分享的Stark-C，如果今天的内容对你有帮助请记得收藏，顺便点点关注，咱们下期再见！谢谢大家~

  


