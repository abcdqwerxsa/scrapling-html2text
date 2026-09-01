# openFuyao技术讲堂 | 容器虚拟机共管

**作者**: openFuyao
**发布时间**: 2026-08-06 18:57
**原文链接**: https://mp.weixin.qq.com/s/ZGDd1aWnTsY0z4j-9qfDvg

---

![](https://r2.jeanjan.kdns.fr/pictures/img-7adc35c101.gif)

前引---云原生时代的虚拟机管理：openFuyao社区基于KubeVirt实现容器与虚拟机统一编排管理能力。

**01**

**特性介绍**

在云原生浪潮席卷IT行业的今天，仍有大量传统应用依赖虚拟机运行--尚未完成容器化改造的企业系统，或是无法容器化的专用服务。如何在统一平台上优雅地管理这两类截然不同的工作负载？KubeVirt由此诞生。

KubeVirt作为由云原生计算基金会（CNCF）赞助的开源项目、红帽OpenShift虚拟化技术的核心底座，旨在将传统虚拟机（VM）工作负载无缝集成到Kubernetes生态中。 通过KubeVirt理念，把虚拟机封装进容器中，纳入Kubernetes声明式API管理，既保留了传统虚拟化的兼容性和隔离性，又能享受Kubernetes提供的编排、调度、网络策略及声明式API等云原生能力。这使得企业能够在统一的混合云平台上平滑迁移和运行遗留应用。

openFuyao 社区在v26.06版本中将KubeVirt深度集成到容器平台，并在鲲鹏（ARM64）服务器环境中完成了从底层虚拟机适配到上层高级能力的全面打通---包括网卡热插拔、macvlan、SR-IOV硬件直通及热迁移、虚拟机热迁移等功能，使企业能够在统一的混合云平台上平滑迁移和应用。

**02**

**应用场景**

  * **边缘计算：** 在边缘计算场景中，往往同时存在新开发的云原生应用和难以容器化的传统服务。KubeVirt允许在边缘Kubernetes集群中统一运行这两类工作负载。 例如：IoT边缘节点可以利用KubeVirt部署基于虚拟机的旧版操作系统服务，同时让该服务与容器化微服务共享底层的网络和存储资源，降低硬件成本并简化管理。

  * **混合云与私有云：** KubeVirt使Kubernetes成为统一的混合云控制平面。通过在裸金属服务器上部署集成了KubeVirt的Kubernetes集群，企业可以实现对虚拟机和容器的统一管理、调度和运维。

**03**

**能力范围**

openFuyao KubeVirt提供从基础到高级的完整虚拟机管理能力。

**基础能力：**

  * **架构支持：** 支持通过声明式CRD（Custom Resource Definition）方式创建ARM64架构的虚拟机。

  * **生命周期管理：** 提供完整的虚拟机基础生命周期管理能力，包括创建、删除、启动、停止及状态同步。

  * **鲲鹏适配：** 支持在鲲鹏节点环境下运行虚拟化工作负载。

**高级能力：**

  * **网卡热插拔：** 为运行中的虚拟机动态添加/删除网卡，无需重启。

  * **macvlan网络：** 让虚拟机直接接入宿主机Underlay网络，绕过Linux网桥，获得接近物理机的网络性能。

  * **SR-IOV硬件直通：** 将物理网卡VF直接挂载到虚拟机，数据不经过宿主机软件模拟层，实现近乎物理机的网络性能。

  * **SR-IOV实时迁移：** 配置SR-IOV直通网卡的虚拟机支持在线热迁移，迁移后通过静态MAC/IP保障网络快速恢复。

  * **虚拟机热迁移：** 支持ARM虚拟机在线热迁移、暂停/恢复、快照等能力。

  * **界面管理：** openFuyao管理面支持对virtualmachines.kubevirt.io资源的创建、删除、开关机等生命周期操作。

**04**

**实现原理**

KubeVirt通过扩展Kubernetes API来管理虚拟机，其核心组件部署在kubevirt命名空间中，如图1所示

**图1** KubeVirt交互视图

![](https://r2.jeanjan.kdns.fr/pictures/img-7adc35c102.png)

**05**

**安装部署及使用**

1、基础环境准备：在所有节点安装KVM相关依赖包，并通过virt-host-validate qemu验证节点虚拟机支持能力。

2、KubeVirt部署：依次安装virt-operator、创建KubeVirt CR实例、验证组件运行状态、安装virtctl命令行工具。

3、制作KubeVirt镜像：下载openEuler ARM64 qcow2镜像，编写Dockerfile将镜像打包进容器，构建并导出为tar包，导入到容器运行时。

4、创建并运行openEuler虚拟机。

详细部署操作步骤请参见使用KubeVirt-操作步骤：

https://docs.openfuyao.cn/zh/docs/v26.06/user_guide/kubevirt.html#%E4%BD%BF%E7%94%A8kubevirt

使用高级虚拟机化管理能力详情请参见使用高级虚拟机化管理能力：

https://docs.openfuyao.cn/zh/docs/v26.06/user_guide/kubevirt.html#%E4%BD%BF%E7%94%A8%E9%AB%98%E7%BA%A7%E8%99%9A%E6%8B%9F%E5%8C%96%E7%AE%A1%E7%90%86%E8%83%BD%E5%8A%9B

**06**

**未来展望**

未来openFuyao社区将基于KubeVirt继续深耕ARM64生态，携手鲲鹏等硬件伙伴，打造兼具亲和力与高性能的虚拟化底座。同时，我们将全面补齐x86平台的高阶特性支持，包括HugePage、NUMA亲和、卷热插拔和内存导出等关键能力。此外，我们将紧密贴合伙伴的实际业务场景，持续打磨并构建更具竞争力的虚拟化解决方案，助力用户实现高效、灵活的云原生部署。

**07**

**资源参考**

openFuyao v26.06版本软件包下载地址：

https://www.openFuyao.cn/zh/download/

**往期推荐**

[![](https://r2.jeanjan.kdns.fr/pictures/img-7adc35c104.png)](https://mp.weixin.qq.com/s?__biz=Mzk3NTk0NDEyMw==&mid=2247487477&idx=1&sn=33d43f3f78076f8af72a8ee4938f75fd&scene=21#wechat_redirect)

  

openFuyao技术讲堂 | Mooncake Store热点缓存优化

[![](https://r2.jeanjan.kdns.fr/pictures/img-7adc35c106.png)](https://mp.weixin.qq.com/s?__biz=Mzk3NTk0NDEyMw==&mid=2247487431&idx=1&sn=b16d2545ce6026e47b90357da8643eca&scene=21#wechat_redirect)

openFuyao技术讲堂 | AI推理赫尔墨斯智能路由（Hermes-router）

[![](https://r2.jeanjan.kdns.fr/pictures/img-7adc35c108.png)](https://mp.weixin.qq.com/s?__biz=Mzk3NTk0NDEyMw==&mid=2247487383&idx=1&sn=9ecac4f421b57b0889cbd049bf9d4248&scene=21#wechat_redirect)

openFuyao技术讲堂 | AI推理鹰眼（Eagle Eye）

![](https://r2.jeanjan.kdns.fr/pictures/img-7adc35c109.png)

