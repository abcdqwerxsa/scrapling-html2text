# NVIDIA Dynamo 与 llm-d 全面对比：分布式大模型推理平台如何选型

**作者**: 原生引擎
**发布时间**: 2026-09-04 14:38
**原文链接**: https://mp.weixin.qq.com/s/gEK3dsQLGdGlZ4zAWAdtcw

---

大模型推理框架正在从“单机跑得快”走向“集群整体效率高”。当模型需要跨多张 GPU 部署，或者线上流量同时包含长 Prompt、长输出、多轮对话和突发请求时，仅依靠 vLLM、SGLang 或 TensorRT-LLM 的单实例能力已经不够。

生产系统还需要解决一组集群级问题：请求应该发给哪个副本，怎样提高 KV Cache 命中率，Prefill 和 Decode 是否应拆开部署，KV Cache 如何跨节点传输，副本怎样扩缩容，以及如何在吞吐、首 Token 延迟和成本之间做权衡。

NVIDIA Dynamo 和 llm-d 都试图解决这些问题。二者经常被拿来比较，但也最容易被误解成两种新的推理引擎。实际上，它们与 vLLM、SGLang 并不是简单的替代关系，而是运行在推理引擎之上的分布式服务系统。

> 本文依据 2026 年 9 月的公开项目状态整理；当时官方文档展示的最新版本分别为 Dynamo v1.4.2 和 llm-d v0.9。两个项目都在快速迭代，具体组件名称和支持范围应以部署时使用的版本为准。

## 一、先给结论

如果只记住一句话，可以这样理解：

> Dynamo 更像一套可从本地扩展到 Kubernetes、深度整合路由、KV 传输、性能分析和自动规划的分布式推理框架；llm-d 更像一套以 Kubernetes、Gateway API Inference Extension 和标准云原生组件为中心的分布式推理栈。

两者当前都支持把 vLLM、SGLang 等引擎组织成集群服务，也都覆盖 KV 感知路由、Prefill/Decode 分离、KV Cache 管理、可观测性和自动扩缩容。真正的区别主要是系统边界、控制面的设计方式和默认部署环境。

| 对比维度       | NVIDIA Dynamo                                            | llm-d                                                                  |
|------------|----------------------------------------------------------|------------------------------------------------------------------------|
| 项目定位       | 通用的开源生成式 AI 分布式推理框架                                      | Kubernetes 原生的分布式 LLM 推理栈                                              |
| 默认使用方式     | 本地、Slurm 或 Kubernetes，可按组件渐进采用                           | 以 Kubernetes 为中心，通过标准 CRD、网关和控制器组合能力                                   |
| 核心对象       | Frontend、Router、Worker、Planner、KV Cache Manager、DGD/DGDR | Router、InferencePool、Model Server，以及 EPP、Variant 等对象                   |
| 推理引擎       | vLLM、SGLang、TensorRT-LLM                                 | 以 vLLM、SGLang 等 Model Server 为执行后端                                     |
| 请求入口       | Dynamo Frontend，或结合 GAIE 的网关模式                           | 生产级 L7 Proxy + Endpoint Picker（EPP）                                    |
| 智能路由       | 负载感知、KV Cache 感知，可消费真实 KV 事件或使用近似状态                      | 插件化 Filter、Scorer、Picker，支持负载、KV、优先级和预测延迟等信号                           |
| P/D 分离     | 原生定义 Prefill、Decode Worker，由 NIXL 传输 KV Cache            | EPP 选择 P/D 端点，Routing Proxy Sidecar 编排引擎协议，重点使用 NIXL                   |
| 自动规划       | Profiler、AIConfigurator、Planner、DGDR，强调由硬件、模型和 SLA 生成部署  | HPA/KEDA 与 Workload Variant Autoscaler，强调 Kubernetes 弹性与跨 Variant 成本优化 |
| 标准化方向      | 提供自己的运行时与 Kubernetes CRD，同时支持 GAIE                       | 深度围绕 Kubernetes Gateway API Inference Extension 构建                     |
| 硬件范围       | NVIDIA、AMD GPU 与 Intel XPU                               | GPU、TPU、XPU、CPU 及部分新型 NPU                                              |
| 社区与治理      | NVIDIA 主导的开源项目                                           | CNCF Sandbox 项目，强调多厂商云原生生态                                             |
| 更适合优先评估的场景 | 希望获得一体化性能工程、自动选型、NIXL 集成，或需要在 K8s 之外运行                   | 已有成熟 K8s/Gateway 体系，希望采用开放标准和可组合云原生组件                                  |

这张表不是性能排行榜。两者都可以构建非常相似的推理拓扑，实际性能更多取决于模型、推理引擎、并行策略、GPU、网络、请求分布和具体配置。

## 二、它们与 vLLM、SGLang 是什么关系

理解 Dynamo 与 llm-d，首先要区分“推理引擎”和“分布式推理平台”。

vLLM、SGLang、TensorRT-LLM 主要负责单个模型实例内部的工作，例如：

  * 加载模型权重；
  * 执行 Transformer 或 MoE 前向计算；
  * Continuous Batching；
  * 管理实例内部的 KV Cache；
  * 执行 Attention、GEMM、量化和推测解码；
  * 使用 Tensor Parallel、Pipeline Parallel 或 Expert Parallel 运行模型。

Dynamo 和 llm-d 则把关注点提高到服务池和集群层面：

```

用户 / Agent / 应用
          │
          │ OpenAI 兼容请求
          ▼
网关、Frontend 或 Proxy
          │
          ▼
集群级路由与流量控制
          │
          ├── 根据负载选择实例
          ├── 根据 KV Cache 位置选择实例
          ├── 选择 Prefill 与 Decode 实例
          └── 执行排队、限流和策略判断
          │
          ▼
vLLM / SGLang / TensorRT-LLM
          │
          ▼
GPU / TPU / XPU / CPU 与网络、内存、存储
```

因此，选择 Dynamo 或 llm-d 并不意味着放弃 vLLM 或 SGLang。更准确的问题应该是：

> 使用哪套集群控制面，把现有推理引擎组织成可扩展、可路由、可观测的生产服务？

## 三、为什么单机推理引擎还不够

### 3.1 普通负载均衡不了解 LLM 状态

传统的 Round Robin 或最少连接数算法只看到 HTTP 连接和请求数量，看不到每个模型实例的真实工作状态。

两个副本可能拥有相同的并发请求数，但它们的负载完全不同：

  * 一个正在处理多个长 Prompt，Prefill 计算压力很高；
  * 一个正在生成大量 Token，Decode 和 KV 显存压力很高；
  * 一个已经缓存了新请求的大部分公共前缀；
  * 一个虽然请求较少，但 KV Cache 已接近耗尽。

如果路由器不了解 Token 数、KV Cache、队列和推理阶段，就很容易把请求送到错误的副本。

### 3.2 Prefill 与 Decode 的资源特征不同

自回归大模型推理可以粗略分成两个阶段：

| 阶段      | 工作内容                                 | 主要压力                  |
|---------|--------------------------------------|-----------------------|
| Prefill | 一次处理输入 Prompt，生成首 Token 和初始 KV Cache | 更偏计算密集，受输入长度影响大       |
| Decode  | 每轮生成一个或少量 Token，并持续读取 KV Cache       | 更偏显存带宽和容量，受并发与输出长度影响大 |

如果由同一组实例同时处理两种工作，超长 Prefill 可能阻塞正在 Decode 的请求，导致 Token 间延迟抖动。将两者拆成独立资源池后，可以分别选择并行度、实例数量和硬件，并独立扩缩容。

但拆分也会引入新问题：Prefill 生成的 KV Cache 必须快速交给 Decode。跨节点传输速度不够时，节省的计算时间可能全部消耗在网络上。

### 3.3 KV Cache 已经成为集群级资源

共享系统提示词、长文档问答、多轮对话和 Agent 工具定义会产生大量重复前缀。如果相同前缀每次都重新 Prefill，会浪费大量算力。

单实例前缀缓存只能解决局部问题。进入多副本环境后，系统还必须知道：

  * 某段前缀缓存在哪个实例上；
  * 该缓存是否仍然存在；
  * 应该优先复用缓存，还是优先均衡负载；
  * GPU 放不下时，能否卸载到 CPU 或 SSD；
  * Prefill 和 Decode 分离时，缓存怎样跨节点移动。

Dynamo 与 llm-d 的核心价值，正是把这些状态纳入路由、传输和扩缩容决策。

## 四、Dynamo 的整体架构

Dynamo 将系统拆分成可以独立采用的组件。一个典型部署包含以下部分：

```

                  ┌──────────────────┐
请求 ────────────▶ │ Dynamo Frontend  │
                  └────────┬─────────┘
                           │
                    KV / Load Router
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Prefill Workers            Decode Workers
              │                         ▲
              └──── KV Cache / NIXL ────┘
 
       Profiler / AIConfigurator / Planner
                 │
                 └── 生成或调整部署规模
```

### 4.1 Frontend 与 KV 感知路由

Dynamo Frontend 接收客户端请求，并为请求选择 Worker。开启 KV 模式后，Router 会同时考虑实例负载和 Prompt 前缀的缓存重叠。

为了获得精确状态，推理 Worker 可以发布 KV Cache 事件，让 Router 知道每个实例当前持有哪些 Cache Block。若后端无法可靠发布事件，Dynamo 也可以根据历史路由结果近似推断缓存状态。

这种路由需要解决一个现实冲突：

  * 请求发往已有缓存的 Worker，可以减少 Prefill、降低 TTFT；
  * 但如果所有相似请求都发往同一 Worker，又可能造成热点、恶化 ITL。

Dynamo 因此在路由评分中同时计算缓存重叠和 Prefill、Decode 负载，并提供参数调节二者权重。它不是简单的“缓存命中优先”，而是一个缓存收益与负载均衡之间的成本模型。

### 4.2 Prefill/Decode 分离与 NIXL

在分离式部署中，Frontend 先把请求送往 Prefill Worker。Prefill 完成后，KV Cache 通过 NIXL 传给 Decode Worker，再由 Decode 持续输出 Token。

NIXL 是 NVIDIA 发起的推理数据传输库。它不是请求调度器，而是负责在 GPU 显存、CPU 内存、网络和存储之间搬运 KV Cache 等数据。Dynamo 将 NIXL 作为 P/D 分离的重要传输层：

  * 同机 GPU 之间可以使用 CUDA IPC、NVLink 等路径；
  * 跨节点通常通过 UCX 和 RDMA 使用 InfiniBand 或 RoCE；
  * 缺少 RDMA 时可以回退到 TCP，但通常只适合开发验证。

Dynamo 官方也特别强调，P/D 分离并不一定更快。小模型、短 Prompt、低并发或网络较慢时，聚合式部署更简单，延迟也可能更低。

### 4.3 DGD、DGDR 与自动部署

在 Kubernetes 中，Dynamo 使用 DynamoGraphDeployment（DGD）描述 Frontend、Prefill Worker、Decode Worker 等服务及其连接关系。

如果团队希望直接控制副本数、并行策略和每个组件的配置，可以手工创建 DGD。如果希望由系统根据目标自动生成配置，则可以使用 DynamoGraphDeploymentRequest（DGDR），结合 Profiler、AIConfigurator 和 Planner 完成：

  1. 识别模型、硬件和可用 GPU；
  2. 评估候选的并行方式与聚合/分离拓扑；
  3. 通过模拟或真实硬件 Profiling 建立性能模型；
  4. 根据 TTFT、ITL、吞吐或成本约束选择配置；
  5. 生成 DGD，并在运行中继续调整副本。

### 4.4 Planner

Dynamo Planner 不只是根据 CPU 或 GPU 利用率扩容。它支持多种优化目标：

  * `throughput`：根据队列和 KV Cache 利用率进行阈值扩缩容；
  * `latency`：更积极地扩容，以减少排队；
  * `load`：使用用户定义的 Prefill 队列 Token 和 Decode KV 利用率阈值；
  * `sla`：结合性能模型，面向具体 TTFT 和 ITL 目标计算副本数量。

在 SLA 模式下，Dynamo 还可以将较慢的预测式容量规划与较快的实时负载响应结合：前者建立稳定容量基线，后者处理突发流量。

这一套 Profiler、性能模型、部署生成和 Planner 的组合，是 Dynamo 很有代表性的能力。它试图把“应该用几张 GPU、P/D 各部署多少副本”从人工经验转化为可重复的工程流程。

### 4.5 部署范围

Dynamo 不把 Kubernetes 作为唯一运行环境。官方文档同时覆盖：

  * 本地或虚拟机直接运行；
  * Kubernetes Operator 和 CRD；
  * Slurm 环境；
  * NVIDIA、AMD GPU 与 Intel XPU；
  * vLLM、SGLang 和 TensorRT-LLM 后端。

这使其既可以作为完整平台，也可以只采用 Frontend、Router、Planner 或 Cache Manager 等部分组件。

## 五、llm-d 的整体架构

llm-d 将核心架构概括为三个对象：Router、InferencePool 和 Model Server。

```

                    ┌──────────────────────┐
请求 ──────────────▶ │ Proxy / Inference GW │
                    └──────────┬───────────┘
                               │ ext-proc
                               ▼
                    ┌──────────────────────┐
                    │ Endpoint Picker EPP  │
                    │ Filter/Score/Pick    │
                    └──────────┬───────────┘
                               │
                        InferencePool
                  ┌────────────┴────────────┐
                  ▼                         ▼
          Model Server Pod          Model Server Pod
          vLLM / SGLang             vLLM / SGLang
```

### 5.1 Router：Proxy 与 EPP 分离

llm-d Router 由两个功能部分组成：

  * Proxy：负责连接管理、TLS、HTTP 转发等标准 L7 数据面能力；
  * Endpoint Picker（EPP）：负责 LLM 专用的端点选择逻辑。

请求到达 Proxy 后会暂时停留，Proxy 通过 ext-proc 协议询问 EPP。EPP 根据 InferencePool 的状态，对候选 Model Server 执行过滤、评分和选择，再把目标地址返回给 Proxy。

这种设计避免重新实现完整网关，而是复用 Envoy、Istio、agentgateway、Envoy AI Gateway 或云厂商负载均衡器等生产级 Proxy，把 llm-d 的重点放在 LLM 感知决策上。

EPP 的调度管线由 Filter、Scorer、Picker 等插件构成，可以综合考虑：

  * 实例负载；
  * KV Cache 亲和性；
  * 请求优先级；
  * 排队和流量控制；
  * 预测 TTFT、ITL 等延迟指标；
  * Prefill 或 Decode 角色。

### 5.2 InferencePool 与 Variant

InferencePool 使用标签选择器把服务同一基础模型的一组 Model Server Pod 组织起来，可以把它理解为 “面向 LLM 优化的 Kubernetes Service”。Router 以 InferencePool 为发现和调度目标。

同一个 Pool 内还可以通过 Pod Label 划分 Variant，例如：

  * Prefill、Decode 或聚合式实例；
  * 高吞吐与低延迟实例；
  * 不同硬件或成本档位；
  * 不同并行度和性能配置。

Variant 不是必须单独创建的 CRD，而是一组具有共同标签和特征的 Pod。这种设计便于在同一逻辑模型下组织异构部署。

### 5.3 KV Cache 管理的三个层次

llm-d 将 KV Cache 管理拆成三个相互配合的层次：

  1. Prefix-Cache Aware Routing：将请求发送给已有相关前缀缓存的实例；
  2. KV-Cache Indexer：消费引擎产生的 KV 事件，跟踪哪些 Block 位于哪些实例或存储层；
  3. KV Offloading：把缓存从加速器 HBM 扩展到 CPU 内存或本地 SSD，形成分层缓存。

路由既可以使用启发式近似状态，也可以使用事件驱动的精确索引。前者部署简单，后者状态更准确，但需要引擎持续发送高频 KV 事件，并考虑索引器自身的扩展和一致性。

### 5.4 Prefill/Decode 分离

llm-d 的 EPP 可以先选择 Decode 端点，再根据 Decode 已缓存的前缀和未命中后缀长度，判断本次请求是否值得走分离路径。如果缓存命中已经足够高，可以直接由 Decode 处理；如果存在较大的未缓存 Prompt，则继续选择 Prefill 端点。

在 Decode Pod 内，Routing Proxy Sidecar 负责把一次用户请求转换为引擎所需的多阶段协议。因为 vLLM 和 SGLang 的 KV 传输控制方式不同，Sidecar 会分别适配：

  * vLLM 的顺序式 Prefill—Decode 协议；
  * SGLang 的并发协调协议。

真正的 KV 数据传输同样重点使用 NIXL。由此可以看到，llm-d 与 Dynamo 在底层技术上并非完全对立：两者都可以使用 vLLM、SGLang 和 NIXL，只是请求编排与控制面的组织方式不同。

### 5.5 延迟预测与自动扩缩容

llm-d 支持通过 Consultant Sidecar 向路由器提供高级信号。其中 Latency Predictor 会在线训练 XGBoost 模型，预测请求的 TTFT 和 ITL，辅助端点评分和 SLO 判断。

扩缩容方面，llm-d 提供两条路径：

  * 使用 HPA/KEDA，根据 EPP 暴露的队列深度等指标进行 Kubernetes 原生扩缩容；
  * 使用 Workload Variant Autoscaler（WVA），在多个 Variant 或 InferencePool 之间进行全局优化，在满足延迟目标的同时尽量降低成本。

因此，llm-d 的自动化思路更偏向将 LLM 指标、异构 Variant 与 Kubernetes 弹性体系结合。

### 5.6 Well-Lit Paths

llm-d 使用 Well-Lit Paths 提供经过测试的部署方案，覆盖：

  * 优化后的基础部署；
  * 预测延迟路由；
  * 精确前缀缓存感知路由；
  * 分层 KV Cache；
  * P/D 分离；
  * MoE Wide Expert Parallelism；
  * 流量控制与公平性；
  * 推理池自动扩缩容；
  * Agent、多模态和批处理工作负载。

它们不是只能原样使用的产品配置，而是面向常见生产模式的基准起点。团队可以在经过验证的路径上替换模型、硬件和参数。

## 六、核心差异分析

### 6.1 系统边界：完整运行时还是 Kubernetes 组合栈

Dynamo 拥有自己的 Frontend、分布式运行组件、Worker 包装层、Router、Planner、Cache Manager 和 Operator，并支持从本地命令逐步扩展到多节点集群。它更愿意定义一套端到端运行时抽象。

llm-d 则尽量复用 Kubernetes 和 Gateway 生态已有能力：Proxy 负责标准网络数据面，EPP 只实现 LLM 专用决策，InferencePool 负责服务发现，Autoscaler 负责副本变化。它更强调把多个云原生项目组合成一套分布式推理栈。

两种路线没有绝对优劣：

  * 一体化系统更容易做跨组件联合优化和自动规划；
  * 标准化组合更容易接入已有网关、平台治理和多厂商环境。

### 6.2 Kubernetes 不是同等程度的前提

llm-d 的核心身份就是 Kubernetes-native。如果团队没有 Kubernetes，使用 llm-d 通常意味着先接受其网关、CRD、控制器和 Pod 调度模型。

Dynamo 同样拥有完整的 Kubernetes 路径，但也可以在本地、虚拟机或 Slurm 上运行。对于研究集群、HPC 环境、单机原型或希望逐步引入组件的团队，Dynamo 的入口更灵活。

### 6.3 路由设计

Dynamo 的常见路径是由 Frontend 同时承担入口和 Worker 选择，也可以接入 GAIE。其 KV Router 与 Worker 的 KV 事件、Dynamo 负载指标和 P/D 拓扑结合紧密。

llm-d 从设计上将 Proxy 与 EPP 分离，并把 Endpoint Picker 作为 Gateway API Inference Extension 的核心实现。对于已经大量使用 Envoy、Istio、Gateway API 和统一入口治理的组织，这种边界通常更加自然。

在算法能力上，两者有很大重叠，都不能简单概括为“一个支持 KV 路由，另一个不支持”。更实际的差异是：

  * 状态从哪里采集；
  * 路由插件怎样扩展；
  * 多副本路由器怎样保持状态；
  * 路由、排队、限流和 P/D 编排如何组合；
  * 团队更熟悉哪一套可观测和运维体系。

### 6.4 P/D 分离

二者都具备 P/D 分离能力，也都把高性能 KV 传输视为成败关键。

Dynamo 更强调通过统一 Worker 运行时、DGD 拓扑和 NIXL 直接表达分离式部署；llm-d 更强调 EPP 的 Profile Handler、网关转发和 Decode Pod 中的 Sidecar 对不同推理引擎协议进行适配。

如果团队希望框架对引擎、路由和传输做较深的一体化集成，Dynamo 的模型更直接。如果团队希望保留原生 Model Server，并由 Kubernetes 网关与 Sidecar 组合流程，llm-d 的方式更符合云原生习惯。

### 6.5 自动化和容量规划

Dynamo 的特色是从部署前 Profiling 一直延伸到运行时 Planner：它可以根据模型、硬件、并行方式和 TTFT/ITL 目标建立性能模型，并生成或调整部署。

llm-d 的特色则是围绕实时路由指标、HPA/KEDA 和多个 Workload Variant 进行弹性与成本优化，还可以使用在线延迟预测改善每个请求的放置。

可以粗略理解为：

  * Dynamo 更关注“这个模型在这套硬件上应该采用什么拓扑和规模”；
  * llm-d 更关注“这些 Kubernetes 推理池与 Variant 应该怎样路由和弹性伸缩”。

但两者的能力正在相互靠近，不能把这句话视为严格边界。

### 6.6 硬件与厂商中立性

Dynamo 由 NVIDIA 主导，并与 NIXL、TensorRT-LLM、AIConfigurator 等 NVIDIA 推理技术结合紧密。但当前官方文档已经明确支持 AMD GPU 和 Intel XPU，因此不能再把它简单描述成“只能运行在 NVIDIA GPU 上”。

llm-d 是 CNCF Sandbox 项目，架构上强调加速器和基础设施可移植性，官方列出了 GPU、TPU、XPU、CPU 和新型 NPU 等方向。对于多云、多加速器和需要基于开放治理降低厂商绑定风险的组织，这一点很有吸引力。

不过，“框架宣称支持”不等于所有能力在所有硬件上完全对等。P/D 分离、KV 事件、分层缓存和特定并行策略仍然受到推理引擎、驱动、网络和 Backend 完成度的限制。

## 七、功能对照

| 能力            | Dynamo                            | llm-d                                       |
|---------------|-----------------------------------|---------------------------------------------|
| OpenAI 兼容入口   | 支持                                | 支持                                          |
| KV Cache 感知路由 | 支持真实 KV 事件与近似状态                   | 支持近似与事件驱动的精确索引                              |
| 负载感知路由        | 支持                                | 支持                                          |
| 预测延迟路由        | Planner 和性能模型侧重容量与 SLA            | Latency Predictor 可参与单请求端点评分                |
| P/D 分离        | 原生 Worker 角色和 DGD 拓扑              | EPP Profile Handler + Routing Proxy Sidecar |
| KV 跨节点传输      | 重点集成 NIXL                         | 重点集成 NIXL                                   |
| KV Offload    | Cache Manager，并可结合 LMCache 等方案    | KV Offloader 与分层缓存体系                        |
| 自动扩缩容         | Dynamo Planner，支持吞吐、延迟、负载和 SLA 目标 | HPA/KEDA 与 WVA                              |
| 自动生成部署        | DGDR、Profiler、AIConfigurator      | Well-Lit Paths 提供基准方案，控制器和 Autoscaler调整运行规模 |
| 标准网关生态        | 可使用自身 Frontend，也支持 GAIE           | 核心设计围绕 GAIE、Proxy 与 EPP                     |
| Kubernetes 之外 | 本地与 Slurm 是正式路径                   | 主要面向 Kubernetes                             |
| 批处理推理         | 提供相关用例与系统组件                       | Batch Gateway 与 Async Processor 可组合使用       |
| MoE 扩展        | 支持多引擎和分布式并行方案                     | 提供 Wide Expert Parallelism 的 Well-Lit Path  |

## 八、谁的性能更好

没有对所有场景都成立的答案。

首先，Dynamo 和 llm-d 经常使用相同的底层引擎、模型 Kernel 和 KV 传输库。一次测试的差异可能来自：

  * vLLM 或 SGLang 版本；
  * Attention、MoE 和 GEMM Backend；
  * Tensor Parallel、Data Parallel 或 Expert Parallel 配置；
  * Prefill 和 Decode 副本比例；
  * KV Cache Block 大小与数据类型；
  * 路由器缓存状态的准确性；
  * 请求的输入、输出长度与前缀重复率；
  * NVLink、InfiniBand、RoCE、EFA 或 TCP；
  * 扩缩容时模型加载和 Warm-up 时间。

其次，官网上的性能数字通常来自不同模型、不同硬件和不同流量，不能横向拼成排行榜。公平测试至少应该统一：

  1. 模型仓库、Revision、精度和量化方式；
  2. 推理引擎与 Kernel 版本；
  3. GPU、网络、容器资源和并行策略；
  4. 聚合式或 P/D 分离拓扑；
  5. 输入长度、输出长度、并发和请求到达分布；
  6. 共享前缀比例与会话持续时间；
  7. TTFT、ITL/TPOT、吞吐、P95/P99 和错误率；
  8. 路由、KV 传输、扩缩容和节点故障期间的稳定性。

尤其要单独测试下面四类流量：

| 流量类型              | 主要验证目标                |
|-------------------|-----------------------|
| 随机独立 Prompt       | 通用负载均衡、批处理和引擎吞吐       |
| 固定长 System Prompt | KV 感知路由与缓存命中收益        |
| 长文档、多问题           | Prefill 压力、TTFT 和缓存淘汰 |
| 多轮 Agent 与长输出     | 会话亲和性、Decode 压力和尾延迟   |

如果没有高速 RDMA 网络，还应将聚合式部署作为基线。P/D 分离的理论优势很容易被 KV Cache 跨节点传输成本抵消。

## 九、怎样选型

### 9.1 优先评估 Dynamo 的情况

  * 不希望把 Kubernetes 作为唯一运行环境，还需要本地、虚拟机或 Slurm；
  * 希望使用统一框架打通 Frontend、Worker、KV 路由、NIXL 和 Planner；
  * 需要根据模型、硬件和 TTFT/ITL 目标自动生成部署配置；
  * 计划深度使用 TensorRT-LLM 或 NVIDIA 的推理性能工具链；
  * 希望先采用某个组件，再逐渐扩展为完整分布式系统；
  * 团队更看重一体化性能工程和部署自动化。

### 9.2 优先评估 llm-d 的情况

  * 已有成熟 Kubernetes、Gateway API、Envoy 或 Istio 平台；
  * 希望路由逻辑与标准 L7 Proxy 解耦；
  * 需要用 InferencePool 和 Variant 表达多种模型服务配置；
  * 重视多厂商硬件、多云部署和 CNCF 生态治理；
  * 希望采用可插拔 Filter、Scorer、Picker 和策略化流量控制；
  * 希望从经过测试的 Well-Lit Paths 起步，并与现有 HPA/KEDA 体系结合。

### 9.3 两者都值得实测的情况

  * 部署超大 MoE 模型；
  * 需要跨节点 P/D 分离；
  * 流量包含大量共享前缀或 Agent 会话；
  * 需要分层 KV Cache 和 CPU/SSD Offload；
  * 同时追求低 TTFT、稳定 ITL 和较高 GPU 利用率；
  * 计划根据 SLA 做自动容量规划。

这些场景中，架构图上的差异不足以直接决定结果。更稳妥的做法是选择同一底层引擎和模型，用真实流量分别实现一个最小生产拓扑，再比较 Goodput、P99、稳定性和运维复杂度。

## 十、常见误区

### 误区一：Dynamo 是 TensorRT-LLM 的新名字

不是。TensorRT-LLM 是推理引擎，Dynamo 是可以管理 TensorRT-LLM、vLLM 和 SGLang 等后端的分布式推理框架。

### 误区二：llm-d 就是 vLLM 的 Kubernetes Helm Chart

不是。vLLM 可以作为 llm-d 的 Model Server，但 llm-d 还包含 Router、EPP、InferencePool、KV 索引、P/D 编排、Autoscaler 和 Well-Lit Paths 等集群级能力。

### 误区三：Dynamo 只支持 NVIDIA，llm-d 才支持异构硬件

这个说法已经过时。Dynamo 当前文档明确列出 AMD GPU 和 Intel XPU；llm-d 的硬件覆盖面仍然更强调可移植性，但具体功能需要逐项核对。

### 误区四：启用 P/D 分离就一定能提高吞吐

不一定。P/D 分离增加了路由步骤、KV Cache 传输、连接管理和故障处理成本。只有当 Prefill 与 Decode 的资源需求明显不同，而且传输链路足够快时，它才更可能获得收益。

### 误区五：KV 感知路由只要知道缓存位置就够了

缓存亲和性与负载均衡存在冲突。过度追求命中率会制造热点，只追求负载平均又会重复 Prefill。真正有效的路由需要同时建模缓存收益、排队、Prefill 工作量、Decode 压力和请求优先级。

## 结语

Dynamo 与 llm-d 代表了分布式推理平台的两条路线。

Dynamo 倾向于提供从请求入口、推理 Worker、KV 传输到 Profiling、自动部署和 Planner 的一体化框架，同时允许用户在本地、Slurm 或 Kubernetes 上按需采用组件。

llm-d 倾向于使用 Kubernetes、Gateway API Inference Extension、生产级 Proxy 和可插拔控制器构建开放的云原生推理栈，把 Model Server、路由、缓存索引和弹性能力组合起来。

两者并不是完全互斥的技术阵营。它们可以使用相同的 vLLM、SGLang 和 NIXL，也在吸收相似的 KV 感知路由、P/D 分离与 SLA 驱动扩缩容思路。

最终选型不应只看“组件是否支持”，而应看这些组件是否能在自己的模型、硬件、网络和真实流量下协同工作。

简而言之：需要跨环境运行、一体化性能规划和更深的运行时整合，可以优先评估 Dynamo；已经全面采用 Kubernetes 和 Gateway 标准、重视开放组合与多厂商生态，可以优先评估 llm-d；对于超大模型和关键生产系统，最终答案应由真实流量下的 TTFT、ITL、Goodput、成本和稳定性共同决定。

## 参考资料

  * NVIDIA Dynamo 官方文档
  * Dynamo Kubernetes Guide
  * Dynamo KV-Aware Routing
  * Dynamo Disaggregated Serving
  * Dynamo Planner
  * Dynamo GitHub
  * llm-d 官方网站
  * llm-d Architecture
  * llm-d Router
  * llm-d KV Cache Management
  * llm-d Disaggregated Serving
  * llm-d Well-Lit Paths
  * llm-d GitHub
  * NIXL GitHub

  


