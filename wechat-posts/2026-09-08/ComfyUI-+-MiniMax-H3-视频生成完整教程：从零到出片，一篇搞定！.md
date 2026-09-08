# ComfyUI + MiniMax H3 视频生成完整教程：从零到出片，一篇搞定！

**作者**: GC随笔
**发布时间**: 2026-08-04 10:39
**原文链接**: https://mp.weixin.qq.com/s/gGGyxahzUa_-CBfzYFkTTg

---

  
![](https://r2.jeanjan.kdns.fr/pictures/img-25384eeb01.png)

> 保姆级教程 | 手把手带你用 ComfyUI 跑通 MiniMax H3 视频模型

## 📌 前言

**ComfyUI** 是目前最强大的模块化 AI 内容创作引擎。它采用**节点/流程图** 界面，让你无需编写任何代码，就能像搭积木一样搭建复杂的 AI 工作流，轻松生成图像、视频、3D 模型、音频等多种内容。

最近，MiniMax 推出的 **H3 视频生成模型** 效果惊艳，在 ComfyUI 中已经可以原生运行。本文将带你从零开始，完整跑通 ComfyUI + MiniMax H3 的视频生成流程！

## 🛠️ 第一步：下载 ComfyUI 官方安装包

首先，从 ComfyUI 官方 GitHub 下载最新的 Windows 便携版（NVIDIA GPU）：

👉 **下载地址：**  
https://github.com/Comfy-Org/ComfyUI/releases/download/v0.30.0/ComfyUI_windows_portable_nvidia.7z

> 📦 该便携版内置 Python 3.13 和 PyTorch CUDA 13.0，解压即用，无需手动配置环境。

下载后使用 **7-Zip** 或新版 Windows 自带的解压工具解压即可。如果解压遇到问题，可以右键文件 → 属性 → 勾选"解除锁定"后再试。

> 💡 **其他版本选择：**
> 
>   * AMD 显卡用户请下载 AMD 版
>   * Intel 显卡用户请下载 Intel 版
>   * 10 系列及更老 N 卡请下载 CUDA 12.6 版
> 

## ⚙️ 第二步：运行自动更新脚本

解压后，先运行自动安装 CUDA 依赖的脚本：

```

📁 你的解压目录\update\update_comfyui_and_python_dependencies.bat
```

这个脚本会自动更新 ComfyUI 核心和所有 Python 依赖到最新版本，耐心等待完成即可。

## 🚀 第三步：启动 ComfyUI

安装完成后，运行 GPU 启动脚本：

```

📁 你的解压目录\run_nvidia_gpu.bat
```

浏览器会自动打开 `http://127.0.0.1:8188`，看到 ComfyUI 的节点编辑界面，说明启动成功！

### 🪶 低显存用户必看

如果你的显卡显存较小（如 8GB 及以下），建议修改启动脚本，加入 `--lowvram` 参数。ComfyUI 拥有**智能内存管理** 机制，最低可在 **1GB 显存** 的 GPU 上运行大模型。

将 `run_nvidia_gpu.bat` 的内容替换为以下脚本：

```

set TRITON_CACHE_DIR=NUL
set TRITON_USE_TCC=0
set SAGEATTN_DISABLE=1
.\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --enable-manager --enable-cors-header --lowvram
echo 如果 ComfyUI 无法启动，请尝试更新 Nvidia 驱动到最新版本。
echo 如果遇到 c10.dll 错误，需要安装 VC Redist：
echo https://aka.ms/vc14/vc_redist.x64.exe
pause
```

**参数说明：**

| 参数                     | 作用                       |
|------------------------|--------------------------|
| `--lowvram`            | 低显存模式，智能卸载不用的模型到内存       |
| `--enable-manager`     | 启用 ComfyUI 管理器，方便安装插件和模型 |
| `--enable-cors-header` | 允许跨域访问（远程调用时有用）          |

## 📥 第四步：下载 MiniMax H3 模型文件

这一步需要下载 **4 个模型文件** ，请按以下路径放置：

| 模型文件                                                | 大小      | 放置路径                           |
|-----------------------------------------------------|---------|--------------------------------|
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`      | 14.6 GB | `ComfyUI\models\text_encoders` |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | 19.5 GB | `ComfyUI\models\unet`          |
| `minimax_h3_audio_vae_fp32.safetensors`             | 577 MB  | `ComfyUI\models\vae`           |
| `minimax_h3_video_vae_fp16.safetensors`             | 4.8 GB  | `ComfyUI\models\vae`           |

> ⚠️ **注意：** 模型总大小约 **40GB** ，请确保硬盘空间充足。建议使用 **固态硬盘（SSD）** 以获得更好的加载速度。

## 🎨 第五步：加载官方工作流并调整参数

使用 ComfyUI 官方提供的 MiniMax H3 工作流模板（可在 ComfyUI 内置的模板列表中找到），然后根据你的硬件配置调整参数。

![](https://r2.jeanjan.kdns.fr/pictures/img-25384eeb02.png)

我下载的是ref2va版本所以支持全能参考的输入。

### 推荐配置参考（8GB 显存 + 16GB 内存 + SSD + 48GB 虚拟内存）

![](https://r2.jeanjan.kdns.fr/pictures/img-25384eeb03.png)

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-25384eeb04.png)  
  
![](https://r2.jeanjan.kdns.fr/pictures/img-25384eeb05.png)

###   

![](https://r2.jeanjan.kdns.fr/pictures/img-25384eeb06.png)

###   

| 视频时长    | 分辨率      | 帧数   | 步数   | 预计耗时        |
|---------|----------|------|------|-------------|
| **7 秒** |  608×352 | 16 帧 | 8 步  | ⏱️ **6 分钟** |
| 7 秒     | 736×416  | 16 帧 | 10 步 | ⏱️ 10 分钟    |

> 🔰 **新手建议：** 第一次跑先用第一个配置（608×352 / 16帧 / 8步）快速验证流程，跑通后再尝试更高参数。

**规律总结：** 分辨率越高、帧数越多、步数越多 → 生成耗时越长，但画质和流畅度也越好。根据你的耐心和需求权衡即可。

## 🧠 ComfyUI 还能做什么？

跑通 MiniMax H3 只是冰山一角！ComfyUI 原生支持大量前沿模型：

### 🖼️ 图像生成

**SDXL / SD3.5 / FLUX / Flux 2 / Hunyuan Image 2.1 / Qwen Image / HiDream / Z Image** 等

### ✏️ 图像编辑

**Flux Kontext / Omnigen 2 / HiDream E1.1 / Qwen Image Edit** 等

### 🎥 视频生成

**Wan 2.1 / Wan 2.2 / Hunyuan Video 1.5 / LTX-Video / Mochi** 等

### 🎵 音频生成

**Stable Audio / ACE Step** 等

### 🧊 3D 模型生成

**Hunyuan3D 2.0** 等

## ⌨️ 常用快捷键速查

| 快捷键            | 功能         |
|----------------|------------|
| `Ctrl + Enter` | 开始生成       |
| `Ctrl + S`     | 保存工作流      |
| `Ctrl + O`     | 加载工作流      |
| `Ctrl + Z / Y` | 撤销/重做      |
| `Delete`       | 删除选中节点     |
| `空格 + 拖拽`      | 移动画布       |
| `双击空白`         | 快速搜索节点     |
| `Ctrl + B`     | 旁路节点（暂时跳过） |
| `Ctrl + M`     | 静音/取消静音节点  |

## 🎯 总结

ComfyUI 作为目前最强大的开源 AI 内容创作引擎，配合 MiniMax H3 这样的顶级视频模型，让 AI 视频创作变得前所未有的简单和可控。本文的流程虽然步骤不少，但每一步都有明确的操作指引，跟着走一遍就能掌握。

希望这篇教程能帮你顺利跑通你的第一条 AI 视频，下一期我们来看看生成的效果如何！如果在操作过程中遇到任何问题，欢迎留言交流 🚀

[开源H3 模型！多张图 + 多段音视频喂进去，直接生成3D短剧实测](https://mp.weixin.qq.com/s?__biz=MzA5OTA5NDQyOQ==&mid=2648513915&idx=1&sn=a2db940fcc51b1ca42b89b29cedad8e8&scene=21#wechat_redirect)

[AI 短剧工业化流程曝光！一套工具走完从剧本到成片](https://mp.weixin.qq.com/s?__biz=MzA5OTA5NDQyOQ==&mid=2648513895&idx=1&sn=b4d60d9231719d831f208ceda6f9f2ad&scene=21#wechat_redirect)

[Agnes API 国内版本上线了，实测效果不错](https://mp.weixin.qq.com/s?__biz=MzA5OTA5NDQyOQ==&mid=2648513882&idx=1&sn=6118ebe0622ec66255da5e696a9d504c&scene=21#wechat_redirect)

[单画布统筹全项目，Krea2 高质量 AI 绘画工作流太丝滑](https://mp.weixin.qq.com/s?__biz=MzA5OTA5NDQyOQ==&mid=2648513866&idx=1&sn=ffe598f59479dcd39587a1e07557aa63&scene=21#wechat_redirect)

[手机跑大模型？Qwen2.5-Omni-3B 端侧部署实战，9大AI场景全解析](https://mp.weixin.qq.com/s?__biz=MzA5OTA5NDQyOQ==&mid=2648513633&idx=1&sn=2d2597fad00a2b4228f368b21caf1b62&scene=21#wechat_redirect)

> 📢 **关注我，获取更多 AI 创作干货教程，下载不到官方全能参考的工作流可以关注后台留言，“H3”，可以自动获取json文件！**
> 
> 💬 有问题？欢迎在评论区留言讨论

