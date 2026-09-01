# Kubernetes DRA 入门：从 Device Plugin 到 ResourceSlice、DeviceClass、ResourceClaim

**作者**: 平凡小代
**发布时间**: 2026-07-19 19:11
**原文链接**: https://mp.weixin.qq.com/s/n1PUesY_qNkecHPIxzjMaw

---

### 一、为什么要了解 DRA

在 Kubernetes 里使用 GPU，很多人最先接触到的是 Device Plugin。比如使用 NVIDIA GPU 时，Pod 里经常这样写：
```

resources:  
  limits:  
    nvidia.com/gpu: 1
```

这种方式很简单，意思也很直观：我要 1 张 GPU。

但是这种方式表达能力比较有限。Kubernetes 官方 Device Plugin 文档说明，扩展资源只支持整数资源，不能超卖，设备也不能在容器之间共享。

也就是说，传统 Device Plugin 更擅长表达“我要几个设备”，但不太擅长表达“我要什么类型的设备、我要满足什么属性的设备、我要显存大于多少的设备、我要让调度器在调度阶段理解具体设备信息”。

这就是 DRA 想解决的问题。

DRA，全称 Dynamic Resource Allocation，可以理解为 Kubernetes 原生的动态设备申请与分配框架。它不是 GPU 虚拟化方案，也不是专门只给 GPU 用的功能，而是 Kubernetes 为 GPU、TPU、FPGA、高性能网卡、RDMA 等异构设备提供的一套更灵活的资源申请与分配机制。

### 二、什么是 DRA

DRA 的核心思想是：不要再只把设备看成一个简单的整数，而是把设备变成 Kubernetes 可以理解的资源对象。

在 DRA 里，几个核心对象可以先这样理解：
```

DRA driver 负责发现和上报设备  
ResourceSlice 表示真实设备清单  
DeviceClass 表示设备类别  
ResourceClaim 表示设备申请  
ResourceClaimTemplate 表示申请模板
```

一句话概括：
```

ResourceSlice 说“集群里有什么设备”  
DeviceClass 说“这些设备可以按什么类别申请”  
ResourceClaim 说“用户想申请什么设备”  
ResourceClaimTemplate 说“如何给多个 Pod 自动生成申请单”  
DRA driver 负责“发现、上报、准备和清理设备”
```

Kubernetes 官方文档中说明，DRA 使用 `resource.k8s.io/v1` API 里的 `DeviceClass`、`ResourceClaim`、`ResourceClaimTemplate`、`ResourceSlice` 来提供核心的设备分配能力。

### 三、DRA 和 Device Plugin 有什么区别

Device Plugin 和 DRA 都和设备资源有关，但它们的表达方式不一样。

| 对比项      | Device Plugin                         | DRA                                       |
|----------|---------------------------------------|-------------------------------------------|
| 典型申请方式   | `resources.limits: nvidia.com/gpu: 1` | `ResourceClaim` / `ResourceClaimTemplate` |
| 资源表达     | 主要表达整数数量                              | 可以表达设备类别、属性、容量、选择条件                       |
| 调度器看到的信息 | 通常主要看节点上的扩展资源数量                       | 可以结合 `ResourceSlice` 中的设备信息做分配            |
| 设备分类     | 通常通过不同扩展资源名区分                         | 通过 `DeviceClass` 表达设备类别                   |
| 设备申请     | 写在 Pod 容器资源限制里                        | 通过 claim 申请，再由 Pod 引用                     |
| 适合场景     | 简单申请一张卡或多个设备                          | 需要按型号、属性、容量等条件选择设备                        |

这里有一个容易说错的点：不能简单说 Device Plugin 下调度器完全不参与。

更准确的说法是：Device Plugin 会把资源上报到 Node 的 `capacity` / `allocatable` 中，调度器会根据这些扩展资源数量做节点过滤。但是在传统 Device Plugin 模式下，调度器通常不知道具体 GPU 的型号、UUID、PCI 地址、显存等更细的信息。

DRA 的不同点在于，它把设备信息通过 `ResourceSlice` 暴露出来，再结合 `DeviceClass` 和 `ResourceClaim` 进行匹配。这样 Kubernetes 就不只是知道“这个节点有几张卡”，还可以理解“这些卡是什么设备、属于哪类、有什么属性、应该如何被申请和分配”。

### 四、DRA driver 是什么

DRA driver 不是一个 Kubernetes API 对象，而是运行在集群里的驱动组件。它通常由硬件厂商、云厂商或者平台团队提供。对于 Kubernetes 来说，DRA driver 是连接 Kubernetes 和真实设备的桥梁。

DRA driver 主要负责发现节点上或者资源池里的设备，创建和更新 `ResourceSlice`，可选地创建 `DeviceClass`，并在 Pod 启动前准备设备，让容器最终能够访问到设备。Pod 删除后，driver 还需要清理相关的设备分配状态。

可以这样理解：
```

Kubernetes 不直接认识每一种硬件  
DRA driver 负责认识硬件  
然后把设备信息用 Kubernetes 能理解的方式发布出来
```

比如某个 GPU DRA driver 启动后，会扫描节点上的 GPU，然后把 GPU 型号、UUID、PCI 地址、显存等信息发布到 `ResourceSlice` 中。

### 五、DeviceClass：设备类别

`DeviceClass` 表示设备类别。它不是具体的设备，而是用户申请设备时看到的分类入口。

例如：
```

kubectl get deviceclass
```

输出类似：
```

NAME                  AGE  
gpu.nvidia.com        5m19s  
mig.nvidia.com        5m19s  
vfio.gpu.nvidia.com   5m19s
```

可以这样理解：

| DeviceClass           | 含义                  |
|-----------------------|---------------------|
| `gpu.nvidia.com`      | 普通 NVIDIA GPU 类别    |
| `mig.nvidia.com`      | NVIDIA MIG 设备类别     |
| `vfio.gpu.nvidia.com` | VFIO / GPU 直通相关设备类别 |

`DeviceClass` 的作用是给用户提供一个稳定的申请入口。用户不一定需要知道底层每张 GPU 的完整属性，只需要说“我要从 `gpu.nvidia.com` 这一类设备里申请资源”。至于这一类设备具体如何筛选，可以由 `DeviceClass` 里的规则来定义。

Kubernetes 官方文档中说明，`DeviceClass` 用来定义可以被 claim 的设备类别，也可以通过 CEL 表达式根据设备属性进行选择。

### 六、ResourceSlice：设备清单

`ResourceSlice` 是 DRA 里非常关键的对象。如果说 `DeviceClass` 是设备类别，那么 `ResourceSlice` 就是真实设备清单。

例如：
```

kubectl get resourceslice -o wide
```

输出可能类似：
```

NAME                                   NODE        DRIVER           POOL        AGE  
00000-gpu.nvidia.com-master-01-zjmb8   master-01   gpu.nvidia.com   master-01   77s
```

这条信息可以拆开理解。

`NAME` 表示：这个 `ResourceSlice` 对象的名字，通常由系统或 driver 自动生成，用户一般不需要手动维护。

`NODE` 表示：这个 `ResourceSlice` 对应哪个节点上的设备。例如这里是 `master-01`。

`DRIVER` 表示：这个 `ResourceSlice` 是由哪个 DRA driver 创建和管理的。例如这里是 `gpu.nvidia.com`。

`POOL` 表示：这些设备属于哪个资源池。可以简单理解为某个 DRA driver 管理的一组设备集合。比如在一个单节点 GPU 环境里，pool 名称可能就是节点名；在更复杂的环境里，一个 driver 也可能按节点、设备组或其他方式组织资源池。

`AGE` 表示：这个对象创建了多久。

所以这条输出整体表示：
```

gpu.nvidia.com 这个 DRA driver  
在 master-01 节点上发现了设备  
并把这些设备信息发布到了名为 master-01 的资源池里
```

正常情况下，`ResourceSlice` 不是用户手动创建的，而是由 DRA driver 自动创建和维护的。用户主要是查看它，用它理解集群里有哪些真实设备，以及这些设备带了哪些属性和容量信息。

查看完整 YAML 时，通常可以看到类似这些信息：
```

spec:  
  driver: gpu.nvidia.com  
  nodeName: master-01  
  pool:  
    name: master-01  
    resourceSliceCount: 1  
  devices:  
  - name: gpu-0  
    attributes:  
      productName:  
        string: NVIDIA GeForce RTX 3070 Ti Laptop GPU  
      uuid:  
        string: GPU-xxxx  
      resource.kubernetes.io/pciBusID:  
        string: "0000:01:00.0"  
      type:  
        string: gpu  
    capacity:  
      memory:  
        value: 8Gi
```

这些字段大致表示：

| 字段                                | 含义                |
|-----------------------------------|-------------------|
| `driver`                          | 由哪个 DRA driver 管理 |
| `nodeName`                        | 设备在哪个节点上          |
| `pool.name`                       | 设备属于哪个资源池         |
| `devices.name`                    | 设备名称              |
| `productName`                     | GPU 型号            |
| `uuid`                            | GPU UUID          |
| `resource.kubernetes.io/pciBusID` | PCI 地址            |
| `capacity.memory`                 | 设备容量信息，例如显存       |

需要注意的是，`attributes` 和 `capacity` 里具体有哪些字段，取决于具体的 DRA driver。Kubernetes 提供的是框架，不同 driver 会发布不同的设备属性。

### 七、ResourceClaim：设备申请单

`ResourceClaim` 表示用户对设备的申请。用一句话理解，它就是“我要什么设备”的申请单。

它会引用某个 `DeviceClass`，然后表达自己想申请什么样的设备。例如：
```

apiVersion: resource.k8s.io/v1  
kind: ResourceClaim  
metadata:  
  name: example-gpu-claim  
spec:  
  devices:  
    requests:  
    - name: gpu  
      exactly:  
        deviceClassName: gpu.nvidia.com  
        allocationMode: ExactCount  
        count: 1
```

这段配置表达的意思是：我要从 `gpu.nvidia.com` 这个 `DeviceClass` 里申请 1 个设备。

如果只看对象关系，可以这样记：
```

DeviceClass 定义“可以申请哪一类设备”  
ResourceClaim 表达“我要从这一类设备里申请什么”  
ResourceSlice 提供“真实有哪些设备可供匹配”
```

调度完成后，`ResourceClaim.status` 中会记录实际分配结果，比如分配到了哪个 driver、哪个 pool、哪个 device，以及这个 claim 当前被哪个 Pod 使用。所以 `ResourceClaim` 不只是一个静态配置，它后面还会承载分配结果。

### 八、ResourceClaimTemplate：申请单模板

`ResourceClaimTemplate` 是 `ResourceClaim` 的模板，它解决的是批量 Pod 的设备申请问题。如果只有一个 Pod，手动创建一个 `ResourceClaim` 还可以接受；但如果是 Deployment、Job、StatefulSet 这类工作负载，可能会创建多个 Pod，这时如果每个 Pod 都需要一份独立的设备申请，就不适合手动写很多个 `ResourceClaim`。

这时候可以使用 `ResourceClaimTemplate`。它的作用是定义一份申请模板，然后由 Kubernetes 自动为 Pod 生成具体的 `ResourceClaim`。

例如：
```

apiVersion: resource.k8s.io/v1  
kind: ResourceClaimTemplate  
metadata:  
  name: single-gpu-template  
spec:  
  spec:  
    devices:  
      requests:  
      - name: gpu  
        exactly:  
          deviceClassName: gpu.nvidia.com  
          allocationMode: ExactCount  
          count: 1
```

这里有一个看起来容易疑惑的地方：
```

spec:  
  spec:
```

这不是写错。第一层 `spec` 是 `ResourceClaimTemplate` 自己的规格，第二层 `spec` 是将来生成出来的 `ResourceClaim.spec`。

可以这样记：
```

ResourceClaimTemplate 不是最终申请单  
它是用来生成 ResourceClaim 的模板
```

`ResourceClaim` 和 `ResourceClaimTemplate` 的选择可以这样理解：

| 场景                              | 建议使用                  |
|---------------------------------|-----------------------|
| 手动管理一个设备申请                      | ResourceClaim         |
| 多个 Pod 每个都要独立申请设备               | ResourceClaimTemplate |
| Deployment / Job 这类工作负载批量创建 Pod | ResourceClaimTemplate |
| 想保留一个独立的申请对象                    | ResourceClaim         |

Kubernetes 官方文档中说明，`ResourceClaimTemplate` 用于让 Kubernetes 为 workload 创建 per-Pod 的 `ResourceClaim`，生成出来的 claim 会和对应 Pod 生命周期绑定。Kubernetes ResourceClaims and ResourceClaimTemplates

### 九、常见误区

#### 误区一：DRA 等于 GPU 虚拟化

这个说法不准确。DRA 是 Kubernetes 的设备申请与分配框架，它本身不等于 GPU 虚拟化。

DRA 负责的是设备如何表达、设备如何申请、设备如何参与调度、设备如何分配给 Pod。至于显存隔离、算力隔离、时间片、公平性这些能力，需要看具体 driver 或底层方案是否支持。

#### 误区二：ResourceSlice 需要用户手写

一般不需要。`ResourceSlice` 通常由 DRA driver 自动创建和维护。用户主要是查看它，用它来理解集群中有哪些设备，以及这些设备带了哪些属性。

日常使用时，用户更常创建的是 `ResourceClaim` 或 `ResourceClaimTemplate`。

#### 误区三：DeviceClass 就是具体 GPU

不是。`DeviceClass` 是设备类别，不是某一张具体 GPU。

比如 `gpu.nvidia.com` 表示一类可申请的 GPU 设备，而不是某一张具体显卡。真正的设备清单在 `ResourceSlice` 里。

#### 误区四：ResourceClaimTemplate 就是 ResourceClaim

不是。`ResourceClaimTemplate` 是模板，`ResourceClaim` 是具体申请单。

可以这样理解：
```

ResourceClaimTemplate 是模具  
ResourceClaim 是用模具生成出来的申请单
```

#### 误区五：Device Plugin 下调度器完全不参与

这个说法也不准确。Device Plugin 模式下，调度器会根据节点上的扩展资源数量做调度判断。

比如某个节点上报了：
```

nvidia.com/gpu: 1
```

Pod 申请：
```

nvidia.com/gpu: 1
```

调度器会判断哪个节点有足够的 `nvidia.com/gpu` 资源。但传统 Device Plugin 模式下，调度器通常只知道数量，不知道具体设备属性。DRA 则进一步把设备属性、类别和申请条件对象化。

#### 误区六：有 ResourceSlice 就表示 Pod 一定能用到设备

不一定。`ResourceSlice` 只能说明 DRA driver 已经把设备清单发布出来了。

Pod 最终能不能用到设备，还要看 `DeviceClass` 是否存在、`ResourceClaim` 是否写对、Pod 是否正确引用 claim、调度器是否成功完成分配、kubelet 是否成功调用 driver 准备设备、容器运行时是否能正确挂载或注入设备。

所以 `ResourceSlice` 是 DRA 工作链路里的重要一环，但不是全部。

### 十、最后总结

DRA 是 Kubernetes 原生的动态设备申请与分配框架。它不是 GPU 虚拟化本身，也不是简单把 `nvidia.com/gpu: 1` 换一种写法。

它真正重要的地方在于：让 Kubernetes 可以用更结构化的方式理解设备。

几个核心对象可以这样记：
```

DRA driver：发现、上报、准备和清理设备  
ResourceSlice：真实设备清单，说明集群里有什么设备  
DeviceClass：设备类别，说明用户可以申请哪类设备  
ResourceClaim：设备申请单，说明用户想要什么设备  
ResourceClaimTemplate：申请单模板，用来自动生成 ResourceClaim
```

如果用一句话收尾：
```

Device Plugin 更像是告诉 Kubernetes“这个节点有几个设备”；  
DRA 则进一步告诉 Kubernetes“这些设备是什么、属于哪类、有什么属性、应该如何被申请和分配”。
```

  


