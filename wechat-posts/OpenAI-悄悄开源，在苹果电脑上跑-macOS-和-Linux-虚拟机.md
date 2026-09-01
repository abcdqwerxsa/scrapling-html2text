# OpenAI 悄悄开源，在苹果电脑上跑 macOS 和 Linux 虚拟机

**作者**: Ai学习的老章
**发布时间**: 2026-07-11 18:08
**原文链接**: https://mp.weixin.qq.com/s/fA4HTvluaF7k7xwl885mrA

---

![](https://r2.jeanjan.kdns.fr/pictures/img-03cdaa3801.png)

大家好，我是 Ai 学习的老章

今天聊个有点意思的东西——OpenAI 悄悄在 GitHub 上挂了个虚拟化项目叫 Tart，专门在 Apple Silicon 上跑 macOS 和 Linux 虚拟机

### 这东西是干啥的

Tart 是一个虚拟化工具集，用来在 Apple Silicon（M1/M2/M3/M4）上构建、运行和管理 macOS 和 Linux 虚拟机

听起来平平无奇对不对？但它有几个杀手锏：

  * **用的是苹果自家的 Virtualization.Framework** ，性能接近原生，不是模拟器那种卡成 PPT 的体验
  * **VM 镜像可以像 Docker 一样 push/pull** ，支持任何 OCI 兼容的容器仓库（ghcr.io、Docker Hub 都行）
  * **Packer 插件自动化构建 VM** ，不用手动一步步装系统
  * **和任何 CI 系统无缝集成** ，天然为自动化而生

说白了，它把虚拟机管理做成了 Docker 那样的体验——`tart clone` 拉镜像，`tart run` 跑虚拟机，`tart push` 推到仓库。对于做 CI/CD 和自动化测试的团队来说，这个工作流太顺了

用一张图看清 Tart 的整体架构：

![](https://r2.jeanjan.kdns.fr/pictures/img-03cdaa3802.png)

### 谁在用

看看用户名单你就知道这不是个玩具项目：

**Atlassian、Figma、Mullvad VPN、Expo、Krisp** 等一票大厂都在内部用

GitHub 上 6.1k star，317 fork，社区还挺活跃

### 为什么 OpenAI 需要它

这里我合理推测一下——OpenAI 大概率是用 Tart 来做 **AI Agent 的沙箱环境**

社区里有个叫 ClodPod 的项目就是很好的例子：它用 Tart 创建一个隔离的 macOS 虚拟机，专门给 Claude Code 跑，只暴露项目目录而不是整个电脑文件系统。这样就可以安全地执行 `claude --dangerously-skip-permissions` 而不怕 Agent 搞坏你的系统

OpenAI 自己的 Codex 等 Agent 类产品，也需要类似的安全沙箱。Tart 这种轻量级、Apple Silicon 原生的虚拟化方案，显然比笨重的传统 VM 方案更适合

### 安装

三行命令搞定：
```

brew install cirruslabs/cli/tart  
tart clone ghcr. io/cirruslabs/macos-tahoe-base:latest tahoe-base  
tart run tahoe-base  

```

第一行装 Tart，第二行从 GitHub Container Registry 拉一个 macOS Tahoe（macOS 26）的基础镜像，第三行直接运行。注意这个镜像大约 25GB，网速慢的话喝杯咖啡

也可以手动安装：
```

curl -LO https://github . com/cirruslabs/tart/releases/latest/download/tart.tar.gz  
tar -xzvf tart.tar.gz  
./tart.app/Contents/MacOS/tart clone ghcr.io/cirruslabs/macos-tahoe-base:latest tahoe-base  
./tart.app/Contents/MacOS/tart run tahoe-base  

```

**系统要求** ：Apple Silicon + macOS 13.0 (Ventura) 及以上

### 核心用法

**SSH 连接 VM** ：
```

ssh admin@$(tart ip tahoe-base)  

```

**目录挂载** （把宿主机目录映射到 VM 里）：
```

tart run --dir=project:~/src/project vm  

```

macOS 客户机会自动挂载到 `/Volumes/My Shared Files/project`，Linux 客户机需要手动 mount：
```

sudo mkdir /mnt/shared  
sudo mount -t virtiofs com.apple.virtio-fs.automount /mnt/shared  

```

**OCI 仓库推送** ：
```

tart push my-local-vm acme.io/org/name:latest acme.io/org/name:v1.0.0  

```

**从零创建 macOS VM** ：
```

tart create --from-ipsw=latest tahoe-vanilla  
tart run tahoe-vanilla  

```

这会下载最新的 macOS IPSW 固件并创建虚拟机，然后你就像装新 Mac 一样走安装流程

### CI/CD 集成

Tart 配合 Cirrus CLI 使用效果最佳。写一个 `.cirrus.yml`：
```

task:  
  name:hello  
macos_instance:  
    image:ghcr.io/cirruslabs/macos-tahoe-base:latest  
hello_script:  
    -echo"Hello from within a Tart VM!"  
    -sysctl-nmachdep.cpu.brand_string  

```

然后：
```

brew install cirruslabs/cli/cirrus  
cirrus run  

```

它会自动拉镜像、启动 VM、拷贝工作目录、执行脚本、收集产物。整个流程和 Docker CI 几乎一样顺滑，但跑的是完整的 macOS 环境

### 和其他方案对比

| 方案            | 性能    | macOS 支持  | OCI 支持 | CI 友好度 |
|---------------|-------|-----------|--------|--------|
| **Tart**      |  接近原生 | 完整        | 原生支持   | 极高     |
| UTM           | 较好    | 支持        | 不支持    | 低      |
| VMware Fusion | 一般    | 支持        | 不支持    | 中      |
| Lima/Colima   | 较好    | 仅 Linux   | 部分     | 中      |
| Docker        | 原生    | 不支持 macOS | 原生     | 极高     |

Tart 的独特定位是：**唯一一个把 Docker 式工作流带到 macOS 虚拟机领域的工具**

###  适合谁用

  1. **iOS/macOS 开发团队** ：跨版本测试（macOS 12-26 全覆盖），不用买一堆真机
  2. **CI/CD 工程师** ：构建 macOS 构建集群，GitHub Actions self-hosted runner
  3. **AI Agent 开发者** ：给 Agent 提供安全沙箱执行环境
  4. **安全研究/恶意软件分析** ：隔离环境，用完即弃

### 总结

Tart 是目前 Apple Silicon 上最优雅的 macOS 虚拟化方案，没有之一。Docker 式的镜像管理 + 原生性能 + CI 原生集成，三个核心卖点都很扎实

唯一的限制是只支持 Apple Silicon（Intel Mac 不行），以及 macOS 13+ 的系统要求。但说实话，2026 年了还在用 Intel Mac 的同学...该升级了

  


