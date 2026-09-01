# WasmEdge：拿下CNCF的WebAssembly运行时，到底有多能打？

**作者**: 知识小零食
**发布时间**: 2026-06-14 08:00
**原文链接**: https://mp.weixin.qq.com/s/Nrr98XM6E-tsQOGRPDvk-Q

---

说真的，WASM这两年几乎是硬生生从浏览器沙盒里杀了出来，一路冲到边缘计算、微服务、甚至AI推理这些领域。但在这些场景里，WASM模块跑在什么地方、怎么跑，就成了一个绕不开的问题。

WasmEdge就是这个问题的答案。它是CNCF官方沙箱项目，一个轻量级、高性能、可扩展的WebAssembly运行时，主打安全隔离和极低的资源消耗。在一篇IEEE论文里，它被评为当今最快的Wasm VM之一。GitHub上已经积累了10k+的star数。更重要的是，WasmEdge最近凭借LlamaEdge项目，变成了在你本地设备上跑LLM的最简单途径。

今天就从零开始，把它用起来。

# 安装：一行命令的事

最省事的办法就是跑官方给的安装脚本。系统需要装好git和curl这两个基础工具。在终端里执行：

```

curl -sSf https://raw.githubusercontent.com/WasmEdge/WasmEdge/master/utils/install.sh | bash
```

跑完之后，再把环境变量配置到当前会话里，这样wasmedge命令才能直接用：

```

source $HOME/.wasmedge/env
```

WasmEdge默认安装在$HOME/.wasmedge目录下，如果你想给系统里所有人用，也可以装到/usr/local去，不过这时候需要在命令前面加上sudo。要是想装特定版本，或者把wasi_nn-ggml这个带LLM推理能力的插件一起带上，也可以给安装脚本传参数。

装完之后验证一下，随便跑个命令：

```

wasmedge --version
```

看到版本号输出了，说明已经就位。

顺便说一句，如果你在用Docker Desktop 4.15+，WasmEdge已经直接打包在里面了，不需要额外安装。

# AoT编译：从解释执行到原生速度

装好之后直接wasmedge跑WASM模块，默认是解释模式——速度不慢，但远不是它的极限。WasmEdge真正厉害的地方在于它内置了一个基于LLVM的AoT编译器（Ahead-of-Time，即提前编译），可以把Wasm字节码提前编译成当前机器的原生指令。

用法出乎意料地简单：

```

wasmedge compile my_app.wasm my_app.so
```

my_app.wasm是你要编译的原始Wasm模块，my_app.so是编译后生成的共享库文件。后面再跑这个应用的时候，直接把这个.so扔给wasmedge执行就行：

```

wasmedge my_app.so
```

如果你的应用涉及数值计算、图像处理或者LLM推理这种重活，AoT带来的性能提升是非常直观的。WasmEdge本身就因为AoT优化，被市场公认为最快的WebAssembly运行时之一。

# 把WASM当容器跑：Docker集成

Docker Desktop 4.15+内置了WasmEdge支持，这意味着你可以用Docker命令直接跑WASM容器，而且这些容器是OCI标准兼容的，可以用docker push推到Docker Hub上。

跑一个最简单的hello world：

```

docker run --rm --runtime=io.containerd.wasmedge.v1 --platform=wasi/wasm secondstate/rust-example-hello:latest
```

注意这里的镜像大小——只有500KB。对比一下，一个普通的Linux容器镜像动辄几十MB甚至上百MB。WASM容器不需要打包任何Linux操作系统库和文件，启动时间也是普通容器的十分之一。

跑一个HTTP微服务也只需要一条命令：

```

docker run -dp 8080:8080 --rm --runtime=io.containerd.wasmedge.v1 --platform=wasi/wasm secondstate/rust-example-server:latest
```

然后curl http://localhost:8080/就能收到响应了。

# 跑LLM：WasmEdge的新赛道

WasmEdge团队基于这个运行时搞了个LlamaEdge项目，号称是“在自己设备上运行定制化LLM最简单最快的方式”。

前提是需要先把带wasi_nn-ggml插件的WasmEdge装上，这一步在前面安装的时候可以一并处理。

然后下载一个GGUF格式的模型文件——这里用Meta Llama 3.2 1B模型做个例子：

```

curl -LO https://huggingface.co/second-state/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q5_K_M.gguf
```

再下载LlamaEdge的CLI聊天应用（也是一个跨平台的Wasm应用）：

```

curl -LO https://github.com/second-state/LlamaEdge/releases/latest/download/llama-chat.wasm
```

最后用wasmedge把模型预加载进去，启动聊天：

```

wasmedge --dir .:. --nn-preload default:GGML:AUTO:Llama-3.2-1B-Instruct-Q5_K_M.gguf llama-chat.wasm -p llama-3-chat
```

这里\--nn-preload参数把GGML格式的模型文件预加载到WasmEdge的神经网路子系统中，-p指定了对话模板。跑完之后你就能在终端里跟本地运行的LLM聊天了。

这事儿要是放在两年前，想在本地跑一个像样的LLM，得上Python、上PyTorch、上一堆依赖。现在一个WasmEdge命令就搞定了，而且整个运行时只有几MB大小，跨平台，在Mac、Windows、Linux、甚至边缘设备上都能跑。基于LlamaEdge，你还可以启动一个与OpenAI API兼容的LLM服务，支持/v1/chat/completion和/v1/embeddings端点，这样任何支持OpenAI API的客户端都可以直接连上来用。

# 一些延伸的方向

WasmEdge的官方文档里列出了相当多的使用场景：边缘云的微服务、无服务器SaaS API、嵌入式函数、区块链智能合约、智能设备应用。它在Serverless领域尤其活跃，很多Serverless平台已经把WasmEdge作为FaaS的底层运行时。同时它也支持通过Go、Rust、C的SDK嵌入到宿主应用中，还可以跟Kubernetes、Docker、Podman这些容器生态工具无缝集成。

WasmEdge做的事情其实并不复杂：它就是一个WASM运行时。但它把这个事情做到了极致——快、轻、安全、可扩展。再加上最近在LLM推理这个方向上的拓展，它从一个“跑WASM模块”的工具，变成了一个“跑AI模型的轻量级引擎”。日常开发里，如果你碰到那种“想跑点东西但又不想起一个Python环境”的场景，用WasmEdge跑个WASM模块往往比折腾一整套依赖要省心得多。

项目地址在这里：https://github.com/WasmEdge/WasmEdge

