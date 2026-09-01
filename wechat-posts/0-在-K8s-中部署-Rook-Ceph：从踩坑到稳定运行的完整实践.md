# 0-在 K8s 中部署 Rook-Ceph：从踩坑到稳定运行的完整实践

**作者**: 驱蚊器喵的插座
**发布时间**: 2026-07-25 02:29
**原文链接**: https://mp.weixin.qq.com/s/cSVN_UAL-L2SdBcNpty8xA

---

> 本文预计阅读时间：30分钟  
> 由于过程比较详细，篇幅较长，建议先收藏

## 前言

在 Kubernetes 集群中部署数据库，离不开可靠的存储。

Kubernetes 支持的存储方案非常多，例如本地存储（Local PV）、NFS、SAN、分布式存储等。

在云环境中，通常可以直接使用云厂商提供的云盘服务；但是在自建机房、离线服务器环境中，更多需要自己建设存储基础设施，例如 NAS、SAN 或 Ceph 这类分布式存储。

考虑到我们的环境主要是裸金属服务器，并且我之前已经有 Ceph 的部署和维护经验，所以最终还是选择 Ceph 作为 Kubernetes 集群的底层存储方案。

虽然很多人认为 Ceph 比较重，学习成本和运维成本都比较高，但经过多年的使用，Ceph 的稳定性和生态已经比较成熟，对于自建 Kubernetes 集群来说，依然是一个非常优秀的选择。

## 我与 Ceph 的几次接触

其实 Ceph 对我来说并不陌生。

目前在现网业务中，我已经部署过两套 Ceph 集群。

第一套：

2021 年 7 月，通过 `ceph-deploy` 离线部署。

当时服务器操作系统还是 CentOS 7，`ceph-deploy` 支持的 Ceph 版本最高停留在 Nautilus（Ceph v14）。

第二套：

2024 年，因为国产化操作系统要求，操作系统切换到了 openeuler 22.03 LTS SP3 （大致兼容 CentOS 8 体系）。

由于操作系统环境变化，原来的部署方式已经不再适用，于是改用 `cephadm` 离线部署， Ceph 版本是 v16.2.8。

从 `ceph-deploy` 到 `cephadm` ，Ceph 的部署方式也经历了一次演进。

## 为什么选择 Rook-Ceph？

`cephadm` 已经采用容器化方式管理 Ceph 服务，相比传统部署方式，在安装、升级、生命周期管理方面更加方便。

但是从 Kubernetes 的角度来看，`cephadm` 依然是一套独立管理的存储系统：

  * • Ceph 集群生命周期由 cephadm 管理；
  * • Kubernetes 只是作为存储消费者使用它；
  * • 两套系统之间仍然存在边界。

既然现在业务已经运行在 Kubernetes 中，那么为什么不直接让 Ceph 也进入 Kubernetes，由 Kubernetes 来统一管理呢？

这也是 Rook-Ceph 出现的意义。

它希望将 Ceph 纳入 Kubernetes 的管理体系：

  * • Ceph 服务运行在 Kubernetes 节点上；
  * • 通过 Operator 管理 Ceph 生命周期；
  * • 使用 CRD 描述 Ceph 集群状态；
  * • 与 Kubernetes 应用共同调度和管理。

  
Ceph 负责“把存储做好”，而 Rook 负责“把 Ceph 在 Kubernetes 里用好”。

## 误解

一开始，我对 Rook-Ceph 有一个误解：

我以为它和传统 Ceph 一样，需要独立部署在 Kubernetes 集群之外，然后通过网络提供存储服务。

因为现网中的其他业务确实采用这种架构，所以在实验环境设计阶段，我最初也是按照“外置 Ceph 存储”的思路规划的。

可以从[0.1-实验环境-一键克隆！制作 openEuler VM 模版（Cloud-Init 实战）](https://mp.weixin.qq.com/s?__biz=MzYyNTE1OTE2Mg==&mid=2247483767&idx=1&sn=f9a7b2d6db89a0063b2e8a0135725f89&scene=21#wechat_redirect)一文中的截图看出，我在实验环境规划 131-133 是3节点的k8s，准备用于安装 rook-ceph，141-148是现网 k8s 的实验环境

后来和 G 老师讨论这个问题时，我才发现：

**Rook-Ceph 的设计理念就是让 Ceph 运行在 Kubernetes 内部，并与 Kubernetes 应用共同管理。**

（所以，实验环境中的 131-133 并没有使用起来，rook-ceph 最终是安装在了 141-148 上，和应用共存）

它通过 Operator 的方式管理 Ceph 集群，将 Ceph 的部署、扩容、故障恢复等操作转换成 Kubernetes 中的声明式资源。

这也是 Rook-Ceph 和传统 Ceph 部署方式最大的区别之一。

## Rook-Ceph 和 Hadoop 的一点类比

我突然想到：这个设计理念是不是 Hadoop 有一些相似之处。

Hadoop 中，DataNode 不仅负责存储数据，也参与计算任务执行。

MapReduce 在调度任务时，会尽量将计算任务安排到数据所在节点附近，也就是 Data Locality（数据本地化）。

原因很简单：

> 移动计算通常比移动大量数据成本更低。

而 Rook-Ceph 也是希望让存储系统进入 Kubernetes 集群内部，不过两者的目标并不完全一样。

Hadoop 强调的是：

> 计算靠近数据。

而 Ceph 强调的是：

> 数据可靠存储和高可用。

对于 Rook-Ceph 来说，Ceph 并不知道 Kubernetes 中具体哪个 Pod 使用了哪些数据，也不会根据应用运行位置主动调整数据分布。

Ceph 关注的是：

  * • PG 状态
  * • OSD 健康
  * • 数据副本
  * • 数据均衡

所以 Rook-Ceph 更准确地说，是：

> 让存储基础设施融入 Kubernetes 生命周期，而不是简单地把 Ceph 容器化。

## 现状

4 月份完成 Kubernetes 集群部署后，目前集群已经稳定运行了几个月。

期间没有出现异常重启或影响业务的故障，目前已经承载了一些实际业务：

  * • 部署了两套 VictoriaMetrics 集群：冷集群使用 HDD 存储池长期存储，热集群使用 SSD 存储池存储最近1个月数据
  * • 通过 VictoriaMetrics 的 vmagent 对约 2000 台服务器进行指标采集；
  * • 部署了 CloudNativePG（CNPG）提供 grafana，netbox，grist 需要的数据库，数据存储在 SSD 存储池
  * • 运行了一些其他业务组件：grafana，netbox，grist

目前来看，集群最大的资源压力主要还是来自 VictoriaMetrics，毕竟监控数据采集规模较大，对存储和 IO 都有一定要求。
```

$ kgp -n rook-ceph  
NAME                                                        READY   STATUS      RESTARTS      AGE  
ceph-csi-controller-manager-67d9b997c9-2l7l6                1/1     Running     3 (79d ago)   81d  
rook-ceph-crashcollector-k8s-octarine-01-76777d5cdc-k5kwv   1/1     Running     0             79d  
rook-ceph-crashcollector-k8s-octarine-02-768b855994-gh8vq   1/1     Running     0             56d  
rook-ceph-crashcollector-k8s-octarine-03-c9887fbc5-k7j2r    1/1     Running     0             56d  
rook-ceph-crashcollector-k8s-octarine-04-64f6d7ccc4-9x4jc   1/1     Running     0             80d  
rook-ceph-crashcollector-k8s-octarine-05-58fc979d59-mmxln   1/1     Running     0             80d  
rook-ceph-exporter-k8s-octarine-01-7b45695dc8-v254n         1/1     Running     0             79d  
rook-ceph-exporter-k8s-octarine-02-79b47f8559-gg4ll         1/1     Running     0             56d  
rook-ceph-exporter-k8s-octarine-03-6c5dbf95cd-rmjgn         1/1     Running     0             56d  
rook-ceph-exporter-k8s-octarine-04-fdd5fc5c5-rhxpj          1/1     Running     0             80d  
rook-ceph-exporter-k8s-octarine-05-6978597b98-pz9sc         1/1     Running     0             80d  
rook-ceph-mds-myfs-a-6dffb866b5-62vxp                       2/2     Running     0             56d  
rook-ceph-mds-myfs-b-df44d4947-k56c6                        2/2     Running     0             56d  
rook-ceph-mgr-a-5f74fd4d48-k27v8                            3/3     Running     6 (78d ago)   80d  
rook-ceph-mgr-b-858bcbffcf-tn6dd                            3/3     Running     0             79d  
rook-ceph-mon-b-694f6c6746-zmjbq                            2/2     Running     0             80d  
rook-ceph-mon-c-6d4547ddcc-v48cd                            2/2     Running     2             80d  
rook-ceph-mon-d-bb58b6565-72v7g                             2/2     Running     4 (79d ago)   80d  
rook-ceph-operator-87698f578-7kjxs                          1/1     Running     0             77d  
rook-ceph-osd-0-59cd749d96-vcx7f                            2/2     Running     0             80d  
rook-ceph-osd-1-f5d7458fc-ffd7z                             2/2     Running     0             80d  
rook-ceph-osd-10-76d4cbbc8c-h27gm                           2/2     Running     0             80d  
rook-ceph-osd-11-6fb7cc79f-b8szx                            2/2     Running     0             80d  
rook-ceph-osd-12-99c646d7b-dfqz7                            2/2     Running     0             80d  
rook-ceph-osd-13-845655859f-g299q                           2/2     Running     0             80d  
rook-ceph-osd-14-b86855769-l9mwn                            2/2     Running     0             80d  
rook-ceph-osd-15-797cf6d979-9g9hv                           2/2     Running     0             80d  
rook-ceph-osd-16-97dc47cbd-gmpcq                            2/2     Running     0             80d  
rook-ceph-osd-17-7b8c9b8f5f-n2l54                           2/2     Running     0             80d  
rook-ceph-osd-18-76bcd9f69f-x2hsr                           2/2     Running     0             80d  
rook-ceph-osd-19-854b7ff569-ct7sh                           2/2     Running     0             80d  
rook-ceph-osd-2-597548b696-rqg4h                            2/2     Running     0             80d  
rook-ceph-osd-20-674bd6488b-zrqpq                           2/2     Running     0             80d  
rook-ceph-osd-21-78dfbf5c66-52s2s                           2/2     Running     0             80d  
rook-ceph-osd-22-ccbd77499-hjzdz                            2/2     Running     0             80d  
rook-ceph-osd-23-55b46bbcc7-gp7sw                           2/2     Running     0             80d  
rook-ceph-osd-24-5d47b58444-vg5kw                           2/2     Running     0             80d  
rook-ceph-osd-25-7c6679d8df-mxhqc                           2/2     Running     0             80d  
rook-ceph-osd-26-6f8f454788-24m2h                           2/2     Running     0             80d  
rook-ceph-osd-27-6dc8c768b7-b6jdm                           2/2     Running     0             80d  
rook-ceph-osd-28-79bff74f85-w2zt2                           2/2     Running     0             80d  
rook-ceph-osd-29-7565f965d6-s8gjz                           2/2     Running     0             80d  
rook-ceph-osd-3-b985f9f89-rcwv5                             2/2     Running     0             80d  
rook-ceph-osd-30-5db5cdc578-r44v2                           2/2     Running     0             80d  
rook-ceph-osd-31-85bf56d94-sbh7j                            2/2     Running     0             80d  
rook-ceph-osd-32-5b865ff587-cqtxq                           2/2     Running     0             80d  
rook-ceph-osd-33-88bcfb55b-g27sr                            2/2     Running     0             80d  
rook-ceph-osd-34-7fc4dc8955-vx5bd                           2/2     Running     0             80d  
rook-ceph-osd-35-69d9877fbd-qb9vg                           2/2     Running     0             80d  
rook-ceph-osd-36-6f9d648f7-hhfdj                            2/2     Running     0             80d  
rook-ceph-osd-37-6fb4798c68-77jml                           2/2     Running     0             80d  
rook-ceph-osd-38-7f48dc597c-tf5pf                           2/2     Running     0             80d  
rook-ceph-osd-39-79cbf758-k5mnw                             2/2     Running     0             80d  
rook-ceph-osd-4-667b466887-ksrsg                            2/2     Running     0             80d  
rook-ceph-osd-40-7bf5455bc6-gq95g                           2/2     Running     2             80d  
rook-ceph-osd-41-85855fd665-zrnwv                           2/2     Running     0             80d  
rook-ceph-osd-42-7cc99f4bcc-sx4rc                           2/2     Running     0             80d  
rook-ceph-osd-43-cb97445fd-dhnpw                            2/2     Running     2             80d  
rook-ceph-osd-44-5bf879ff79-xztst                           2/2     Running     0             80d  
rook-ceph-osd-45-58dbb8f6b5-p89xt                           2/2     Running     0             80d  
rook-ceph-osd-46-7bc94d88c9-nzjcl                           2/2     Running     4 (79d ago)   80d  
rook-ceph-osd-47-7d67849d75-tdbws                           2/2     Running     4 (79d ago)   80d  
rook-ceph-osd-48-5c67c6c5b5-h2ljn                           2/2     Running     0             80d  
rook-ceph-osd-49-5cf7b8df6c-hq2nk                           2/2     Running     0             80d  
rook-ceph-osd-5-588bbb4b66-lbpqk                            2/2     Running     0             80d  
rook-ceph-osd-6-cd4559876-xllj6                             2/2     Running     0             80d  
rook-ceph-osd-7-6bbb5cf5c4-rwbs9                            2/2     Running     0             80d  
rook-ceph-osd-8-7c89b646c4-ztwp4                            2/2     Running     0             80d  
rook-ceph-osd-9-688f557f59-8td5f                            2/2     Running     0             80d  
rook-ceph-osd-prepare-k8s-octarine-01-kpprm                 0/1     Completed   0             77d  
rook-ceph-osd-prepare-k8s-octarine-02-f6d2l                 0/1     Completed   0             77d  
rook-ceph-osd-prepare-k8s-octarine-03-lsb9n                 0/1     Completed   0             77d  
rook-ceph-osd-prepare-k8s-octarine-04-fnqkh                 0/1     Completed   0             77d  
rook-ceph-osd-prepare-k8s-octarine-05-mp8s9                 0/1     Completed   0             77d  
rook-ceph-tools-c698b4847-jkck4                             1/1     Running     0             79d  
rook-ceph.cephfs.csi.ceph.com-ctrlplugin-85d586d669-5fr5h   5/5     Running     12            81d  
rook-ceph.cephfs.csi.ceph.com-ctrlplugin-85d586d669-ctt5s   5/5     Running     1 (80d ago)   81d  
rook-ceph.cephfs.csi.ceph.com-nodeplugin-7mjc6              2/2     Running     0             77d  
rook-ceph.cephfs.csi.ceph.com-nodeplugin-97zf5              2/2     Running     0             77d  
rook-ceph.cephfs.csi.ceph.com-nodeplugin-m55qb              2/2     Running     0             77d  
rook-ceph.cephfs.csi.ceph.com-nodeplugin-s6kdl              2/2     Running     0             77d  
rook-ceph.cephfs.csi.ceph.com-nodeplugin-s6wzt              2/2     Running     0             77d  
rook-ceph.rbd.csi.ceph.com-ctrlplugin-7999c97855-gpm5m      5/5     Running     0             81d  
rook-ceph.rbd.csi.ceph.com-ctrlplugin-7999c97855-rrkh4      5/5     Running     8 (80d ago)   81d  
rook-ceph.rbd.csi.ceph.com-nodeplugin-97r4p                 2/2     Running     0             77d  
rook-ceph.rbd.csi.ceph.com-nodeplugin-cb45p                 2/2     Running     0             77d  
rook-ceph.rbd.csi.ceph.com-nodeplugin-pbwfv                 2/2     Running     0             77d  
rook-ceph.rbd.csi.ceph.com-nodeplugin-td6z8                 2/2     Running     0             77d  
rook-ceph.rbd.csi.ceph.com-nodeplugin-vl9mf                 2/2     Running     0             77d
```

## Rook-Ceph 部署

前面介绍了为什么最终选择 Rook-Ceph，以及当前 Kubernetes 集群的运行情况。

接下来开始正式部署 Rook-Ceph。

由于这是一个已经运行了一段时间的 Kubernetes 集群，并且后续还会继续承载其他业务，所以部署过程中并没有完全按照官方 Quickstart 示例直接执行，而是根据实际环境进行了调整。

主要涉及几个方面：

  * • Ceph 组件的调度策略
  * • master 节点 taint 的处理
  * • OSD 磁盘识别问题
  * • Ceph Toolbox 的使用

本文使用的 Rook 版本为

  * • v1.18.4 （实验环境部署时的最新稳定版本）

Ceph 版本

  * • v19.2.3 （EOL： 2026-09-19）

部署时间

  * • 实验环境：2025 年 10 月
  * • 现网环境：2026 年 4 月

写本文时，Rook 已经更新至 v1.20.2，可以看出其版本迭代较为频繁，整体维护也比较活跃。

需要注意的是，Ceph v19 的生命周期截止时间为 2026-09-19。如果是全新部署，建议优先选择较新的 Rook 版本，从而使用更新的 Ceph 版本，一方面可以获得更完善的功能支持，另一方面也能够规避已知漏洞和潜在问题。

### 准备镜像

images.txt
```

docker.io/rook/ceph:v1.18.4  
gcr.io/k8s-staging-sig-storage/objectstorage-sidecar:v20240513-v0.1.0-35-gefb3255  
quay.io/ceph/ceph:v19.2.3  
quay.io/ceph/cosi:v0.1.2  
quay.io/cephcsi/ceph-csi-operator:v0.4.1  
quay.io/cephcsi/cephcsi:v3.15.0  
quay.io/csiaddons/k8s-sidecar:v0.13.0  
registry.k8s.io/sig-storage/csi-attacher:v4.8.1  
registry.k8s.io/sig-storage/csi-node-driver-registrar:v2.13.0  
registry.k8s.io/sig-storage/csi-provisioner:v5.2.0  
registry.k8s.io/sig-storage/csi-resizer:v1.13.2  
registry.k8s.io/sig-storage/csi-snapshotter:v8.2.1
```

实验环境拉取镜像
```

for i in `cat images.txt`;do echo $i;docker pull $i;done
```

导出镜像
```

image_name=$(paste -sd' ' rook_images.txt)  
docker save $image_name | gzip > rook_ceph_images.tar.gz
```

分发到内网服务器
```

for i in `cat 5_ip`;do echo $i;scp rook_ceph_images.tar.gz $i:/home/<REDACTED>/;done  
for i in `cat 5_ip`;do echo $i;ssh $i "sudo su -c 'ctr -n k8s.io images import /home/<REDACTED>/rook_ceph_images.tar.gz'";done
```

### 开始部署

参考官方文档：

https://rook.github.io/docs/rook/latest-release/Getting-Started/quickstart/#prerequisites

支持的 Kubernetes 版本：v1.31 - v1.36

在实验环境中，通过 Git 拉取对应版本：
```

export HTTPS_PROXY=http://192.168.31.110:7890  
git clone --single-branch --branch v1.18.4 https://github.com/rook/rook.git
```

打包后传到内网环境：
```

tar zxf rook.tar.gz rook
```

按照官方步骤部署：
```

cd rook/deploy/examples  
  
# 创建 CRD 和 Operator  
kubectl create -f crds.yaml -f common.yaml -f csi-operator.yaml -f operator.yaml  
  
# 创建 Ceph 集群  
kubectl create -f cluster.yaml
```

## 启动情况

这是当时的启动情况
```

[<REDACTED>@k8s-octarine-01 examples]$ kubectl -n rook-ceph get pods -o wide  
NAME                                                        READY   STATUS    RESTARTS   AGE   IP               NODE              NOMINATED NODE   READINESS GATES  
ceph-csi-controller-manager-67d9b997c9-2l7l6                1/1     Running   0          48s   10.244.235.194   k8s-octarine-04   <none>           <none>  
rook-ceph-mon-a-6cbdd7f8df-cvkp6                            0/2     Pending   0          24s   <none>           <none>            <none>           <none>  
rook-ceph-operator-5d46d7d965-7v5b9                         1/1     Running   0          48s   10.244.10.66     k8s-octarine-05   <none>           <none>  
rook-ceph.cephfs.csi.ceph.com-ctrlplugin-85d586d669-5fr5h   5/5     Running   0          20s   10.244.241.76    k8s-octarine-01   <none>           <none>  
rook-ceph.cephfs.csi.ceph.com-ctrlplugin-85d586d669-ctt5s   5/5     Running   0          20s   10.244.10.68     k8s-octarine-05   <none>           <none>  
rook-ceph.cephfs.csi.ceph.com-nodeplugin-7n8sd              2/2     Running   0          20s   192.168.2.68    k8s-octarine-04   <none>           <none>  
rook-ceph.cephfs.csi.ceph.com-nodeplugin-dj6x8              2/2     Running   0          20s   192.168.2.69    k8s-octarine-05   <none>           <none>  
rook-ceph.cephfs.csi.ceph.com-nodeplugin-ndgb7              2/2     Running   0          20s   192.168.1.166   k8s-octarine-01   <none>           <none>  
rook-ceph.rbd.csi.ceph.com-ctrlplugin-7999c97855-gpm5m      5/5     Running   0          20s   10.244.10.69     k8s-octarine-05   <none>           <none>  
rook-ceph.rbd.csi.ceph.com-ctrlplugin-7999c97855-rrkh4      5/5     Running   0          20s   10.244.235.197   k8s-octarine-04   <none>           <none>  
rook-ceph.rbd.csi.ceph.com-nodeplugin-99pmp                 2/2     Running   0          20s   192.168.2.68    k8s-octarine-04   <none>           <none>  
rook-ceph.rbd.csi.ceph.com-nodeplugin-kr4w2                 2/2     Running   0          20s   192.168.1.166   k8s-octarine-01   <none>           <none>  
rook-ceph.rbd.csi.ceph.com-nodeplugin-tdnc9                 2/2     Running   0          20s   192.168.2.69    k8s-octarine-05   <none>           <none>
```

## 问题1：mon 个数不够以及需要调整运行节点

部署完成后，可以看到 `mon` 处于 Pending 状态，并且只有 2 个实例。

原因也比较直观：当前只有 2 个 worker 节点。

但在生产环境中，`mon` 需要3个，而且我的 master 节点 内存很富足。  
我的目标是：**将 mon 调度到 3 个 master 节点上。**

查看 Pod 事件可以看到：
```

[<REDACTED>@k8s-octarine-01 examples]$ kubectl describe po rook-ceph-mon-a-6cbdd7f8df-cvkp6 -n rook-ceph  
....  
Events:  
  Type     Reason            Age    From               Message  
  ----     ------            ----   ----               -------  
  Warning  FailedScheduling  3m34s  default-scheduler  0/5 nodes are available: 1 node(s) didn't satisfy existing pods anti-affinity rules, 2 node(s) didn't match Pod's node affinity/selector, 2 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }. preemption: 0/5 nodes are available: 1 node(s) didn't satisfy existing pods anti-affinity rules, 4 Preemption is not helpful for scheduling.
```

问题本质有三个：

  * • ❌ Master 默认带 taint，不允许调度
  * • ❌ Rook 默认有 node affinity 限制
  * • ❌ mon 默认要求分散部署

### 调整调度策略（关键）

修改 CephCluster：
```

kubectl -n rook-ceph edit cephcluster
```

按照官方文档，应该这样调整 placement ，但是实际没有生效
```

spec:  
  mon:  
    count: 3  
  
  placement:  
    # ✅  1. MON 只在 master  
    mon:  
      nodeAffinity:  
        requiredDuringSchedulingIgnoredDuringExecution:  
          nodeSelectorTerms:  
            - matchExpressions:  
                - key: node-role.kubernetes.io/control-plane  
                  operator: Exists  
      tolerations:  
        - key: node-role.kubernetes.io/control-plane  
          operator: Exists  
          effect: NoSchedule  
  
    # ✅  2. OSD 允许上 master（用 master 磁盘）  
    osd:  
      tolerations:  
        - key: node-role.kubernetes.io/control-plane  
          operator: Exists  
          effect: NoSchedule  
  
    # https://github.com/rook/rook/issues/16878  
    prepareosd:  
      tolerations:  
        - key: node-role.kubernetes.io/control-plane  
          operator: Exists  
          effect: NoSchedule
```

实测：针对 mon/osd 单独配置不生效，直接作用到 `all` 才生效。
```

spec:  
  mon:  
    count: 3  
  
  placement:  
    all:  
      tolerations:  
        - key: node-role.kubernetes.io/control-plane  
          operator: Exists  
          effect: NoSchedule
```

### 为什么不去掉 master taint？

这里做了一个取舍：

  * • ❌ 不希望所有业务都能调度到 master
  * • ✅ 只允许特定组件（如 Ceph）容忍 taint

所以选择**增加 toleration，而不是删除 taint**

###  重新应用配置
```

kubectl apply -f cluster.yaml  
  
kubectl -n rook-ceph delete pod -l app=rook-ceph-osd-prepare  
kubectl -n rook-ceph rollout restart deploy rook-ceph-operator
```

最终：

  * • mon 成功扩展到 3 个
  * • 并调度到了 master 节点

## 问题2：OSD 没有分布到所有节点

现象：

  * • 部分节点没有 OSD
  * • `osd-prepare` Pod Pending

和问题1一样，通过调整 placement 解决

## 问题3：如何执行 ceph -s

用过 ceph 的朋友萌都知道，`ceph -s` 是个常见的命令，用于查看 ceph 集群状态，在容器环境，没有 ceph 命令该怎么办呢？

需要部署 toolbox 应用：

这个官方的文件中的镜像版本是 `v19`，我们下载的镜像是 `v19.2.3`，于是修改镜像版本
```

vi rook/deploy/examples/toolbox.yaml

quay.io/ceph/ceph:v19.2.3
```

应用：
```

kubectl apply -f rook/deploy/examples/toolbox.yaml
```

进入容器，也可以不进，直接运行
```

kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph -s  
  cluster:  
    id:     c5760708-2223-4b12-bdc9-1f725018c531  
    health: HEALTH_WARN  
            1/3 mons down, quorum b,c  
  
  services:  
    mon: 3 daemons, quorum b,c (age 8m), out of quorum: a  
    mgr: a(active, since 14m), standbys: b  
    osd: 40 osds: 0 up, 40 in (since 6m)  
  
  data:  
    pools:   0 pools, 0 pgs  
    objects: 0 objects, 0 B  
    usage:   0 B used, 0 B / 0 B avail  
    pgs:
```

这还挺方便的，应该是把 keyring 密钥都挂载进去了，很优雅

## 问题4：OSD 未识别部分磁盘

问题原因：

磁盘存在分区/残留数据，导致 Rook 未识别为可用设备
```

  
[<REDACTED>@k8s-octarine-01 ~]$ lsblk  
NAME   MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS  
sda      8:0    0 893.1G  0 disk  
└─sda1   8:1    0 893.1G  0 part  
sdb      8:16   0 893.1G  0 disk  
└─sdb1   8:17   0 893.1G  0 part  
sdc      8:32   0 446.1G  0 disk  
├─sdc1   8:33   0     1G  0 part /boot  
└─sdc2   8:34   0 445.1G  0 part /  
nbd0    43:0    0     0B  0 disk  
nbd1    43:32   0     0B  0 disk  
nbd2    43:64   0     0B  0 disk  
nbd3    43:96   0     0B  0 disk  
nbd4    43:128  0     0B  0 disk  
nbd5    43:160  0     0B  0 disk  
nbd6    43:192  0     0B  0 disk  
nbd7    43:224  0     0B  0 disk  
nbd8    43:256  0     0B  0 disk  
nbd9    43:288  0     0B  0 disk  
nbd10   43:320  0     0B  0 disk  
nbd11   43:352  0     0B  0 disk  
nbd12   43:384  0     0B  0 disk  
nbd13   43:416  0     0B  0 disk  
nbd14   43:448  0     0B  0 disk  
nbd15   43:480  0     0B  0 disk
```

处理方法：
```

wipefs -n /dev/sdX   # 查看  
wipefs -a /dev/sdX   # 清理  
  
sgdisk --zap-all /dev/sdX # 如果 wipefs 清理不干净，用这个清理
```

### 触发重新扫描

Rook 中的 operator 可以理解为整个 Ceph 集群的“控制平面”，负责资源编排和状态维护。重启 operator 不会影响已经运行的 MON 和 OSD（即数据面不会中断），但在重启期间不会进行新的调度或状态协调。

可以通过以下方式触发重新扫描：
```

# 重启 operator（推荐方式）  
kubectl -n rook-ceph rollout restart deploy rook-ceph-operator  
  
# 删除 osd-prepare pod，触发重新探测磁盘  
kubectl -n rook-ceph delete pod -l app=rook-ceph-osd-prepare  
  
# 或者直接删除 operator pod（效果类似，会自动重建）  
kubectl -n rook-ceph delete pod -l app=rook-ceph-operator
```

删除 operator 后，磁盘重新扫描才生效，在 operator 启动了 20m+ 后，才开始启动 prepare
```

[<REDACTED>@k8s-octarine-01 examples]$ kubectl -n rook-ceph get pod -l app=rook-ceph-operator  
NAME                                  READY   STATUS    RESTARTS   AGE  
rook-ceph-operator-78fd5c89b6-qfhqg   1/1     Running   0          32m  
[<REDACTED>@k8s-octarine-01 examples]$ kubectl -n rook-ceph get pod -l app=rook-ceph-osd-prepare  
NAME                                          READY   STATUS      RESTARTS   AGE  
rook-ceph-osd-prepare-k8s-octarine-01-t946j   0/1     Completed   0          6m1s  
rook-ceph-osd-prepare-k8s-octarine-02-glst4   0/1     Pending     0          6m1s  
rook-ceph-osd-prepare-k8s-octarine-03-vbmsl   0/1     Pending     0          6m1s  
rook-ceph-osd-prepare-k8s-octarine-04-6kwkg   0/1     Completed   0          5m58s  
rook-ceph-osd-prepare-k8s-octarine-05-nclq8   0/1     Completed   0          5m55s
```

  

最终成功识别并创建 OSD。

## 问题5：磁盘类型没有被正确识别

发现部分磁盘未能被 Ceph 正确识别其设备类型（如 HDD / SSD）。

该问题通常与底层硬件配置有关。在本环境中，由于 RAID 卡不支持直通（HBA 模式），因此将每块物理磁盘配置为 RAID0 暴露给操作系统。 （参见前文[1.0-现网实战-openEuler 22.03 基于 kube-vip 离线部署高可用 Kubernetes v1.33.2](https://mp.weixin.qq.com/s?__biz=MzYyNTE1OTE2Mg==&mid=2247483790&idx=1&sn=fc8423d0c6e2547b9ccd167ed1c2655a&scene=21#wechat_redirect)）

这种方式虽然可以让系统识别到独立磁盘，但会导致磁盘的物理属性信息（如 rotational）丢失，从而影响 Ceph 对磁盘类型的判断。

Ceph 在创建 OSD 时，会根据磁盘类型（HDD / SSD / NVMe）进行分类，这对于后续的存储池规划至关重要。例如：

  * • 不同介质适用于不同业务场景（性能 / 成本）
  * • 可以基于 device class 创建不同的 CRUSH rule 和存储池
  * • 上层业务可以按需选择存储池（如高性能 / 大容量）

```

[<REDACTED>@k8s-octarine-01 ~]$ kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph osd tree  
ID  CLASS  WEIGHT     TYPE NAME                 STATUS  REWEIGHT  PRI-AFF  
-1         223.51257  root default  
-7           1.74438      host k8s-octarine-01  
40    hdd    0.87219          osd.40                up   1.00000  1.00000  
43    hdd    0.87219          osd.43                up   1.00000  1.00000
```

master 节点的2个磁盘是 SSD

修改磁盘类型
```

kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- bash  
  
ceph osd crush rm-device-class osd.40  
ceph osd crush rm-device-class osd.43  
  
ceph osd crush set-device-class ssd osd.40  
ceph osd crush set-device-class ssd osd.43
```

操作不会影响磁盘数据

查看
```

[<REDACTED>@k8s-octarine-01 ~]$ kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph osd tree  
ID  CLASS  WEIGHT     TYPE NAME                 STATUS  REWEIGHT  PRI-AFF  
-1         223.51257  root default  
-7           1.74438      host k8s-octarine-01  
40    ssd    0.87219          osd.40                up   1.00000  1.00000  
43    ssd    0.87219          osd.43                up   1.00000  1.00000  
-3         110.88409      host k8s-octarine-04  
 0    hdd    5.45699          osd.0                 up   1.00000  1.00000  
 2    hdd    5.45699          osd.2                 up   1.00000  1.00000  
 5    hdd    5.45699          osd.5                 up   1.00000  1.00000  
 7    hdd    5.45699          osd.7                 up   1.00000  1.00000  
 9    hdd    5.45699          osd.9                 up   1.00000  1.00000  
11    hdd    5.45699          osd.11                up   1.00000  1.00000  
12    hdd    5.45699          osd.12                up   1.00000  1.00000  
14    hdd    5.45699          osd.14                up   1.00000  1.00000  
16    hdd    5.45699          osd.16                up   1.00000  1.00000  
18    hdd    5.45699          osd.18                up   1.00000  1.00000  
20    hdd    5.45699          osd.20                up   1.00000  1.00000  
22    hdd    5.45699          osd.22                up   1.00000  1.00000  
24    hdd    5.45699          osd.24                up   1.00000  1.00000  
26    hdd    5.45699          osd.26                up   1.00000  1.00000  
29    hdd    5.45699          osd.29                up   1.00000  1.00000  
31    hdd    5.45699          osd.31                up   1.00000  1.00000  
33    hdd    5.45699          osd.33                up   1.00000  1.00000  
35    hdd    5.45699          osd.35                up   1.00000  1.00000  
37    hdd    5.45699          osd.37                up   1.00000  1.00000  
39    hdd    5.45699          osd.39                up   1.00000  1.00000  
41    hdd    0.87219          osd.41                up   1.00000  1.00000  
44    hdd    0.87219          osd.44                up   1.00000  1.00000  
-5         110.88409      host k8s-octarine-05  
 1    hdd    5.45699          osd.1                 up   1.00000  1.00000  
 3    hdd    5.45699          osd.3                 up   1.00000  1.00000  
 4    hdd    5.45699          osd.4                 up   1.00000  1.00000  
 6    hdd    5.45699          osd.6                 up   1.00000  1.00000  
 8    hdd    5.45699          osd.8                 up   1.00000  1.00000  
10    hdd    5.45699          osd.10                up   1.00000  1.00000  
13    hdd    5.45699          osd.13                up   1.00000  1.00000  
15    hdd    5.45699          osd.15                up   1.00000  1.00000  
17    hdd    5.45699          osd.17                up   1.00000  1.00000  
19    hdd    5.45699          osd.19                up   1.00000  1.00000  
21    hdd    5.45699          osd.21                up   1.00000  1.00000  
23    hdd    5.45699          osd.23                up   1.00000  1.00000  
25    hdd    5.45699          osd.25                up   1.00000  1.00000  
27    hdd    5.45699          osd.27                up   1.00000  1.00000  
28    hdd    5.45699          osd.28                up   1.00000  1.00000  
30    hdd    5.45699          osd.30                up   1.00000  1.00000  
32    hdd    5.45699          osd.32                up   1.00000  1.00000  
34    hdd    5.45699          osd.34                up   1.00000  1.00000  
36    hdd    5.45699          osd.36                up   1.00000  1.00000  
38    hdd    5.45699          osd.38                up   1.00000  1.00000  
42    hdd    0.87219          osd.42                up   1.00000  1.00000  
45    hdd    0.87219          osd.45                up   1.00000  1.00000
```

如何找出 04 05 节点上的 SSD 盘呢
```

bash-5.1$ ceph osd metadata osd.43 | grep device  
    "bluefs_single_shared_device": "1",  
    "bluestore_bdev_devices": "sdb",  
    "default_device_class": "hdd",  
    "device_ids": "sdb=AVAGO_HW-SAS3408_008a5bb4bcfb2472310030395a84a940",  
    "device_paths": "sdb=/dev/disk/by-path/pci-0000:1c:00.0-scsi-0:2:2:0",  
    "devices": "sdb",  
    "objectstore_numa_unknown_devices": "sdb",
```

这样可以看到 osd 对应的盘符，但是还是很麻烦

从大小入手，查看所有盘大小
```

[<REDACTED>@k8s-octarine-01 ~]$ kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph osd df  
ID  CLASS  WEIGHT   REWEIGHT  SIZE     RAW USE  DATA     OMAP     META     AVAIL    %USE  VAR    PGS  STATUS  
40    ssd  0.87219   1.00000  893 GiB   32 MiB  5.1 MiB    6 KiB   27 MiB  893 GiB  0.00   4.01    0      up  
43    ssd  0.87219   1.00000  893 GiB   32 MiB  5.1 MiB    6 KiB   27 MiB  893 GiB  0.00   3.99    0      up  
46    ssd  0.87219   1.00000  893 GiB   32 MiB  5.1 MiB    4 KiB   27 MiB  893 GiB  0.00   3.96    0      up  
47    ssd  0.87219   1.00000  893 GiB  433 MiB  5.8 MiB    4 KiB   27 MiB  893 GiB  0.05  53.64    1      up  
48    ssd  0.87219   1.00000  893 GiB   67 MiB  5.1 MiB    1 KiB   61 MiB  893 GiB  0.01   8.24    0      up  
49    ssd  0.87219   1.00000  893 GiB   67 MiB  5.1 MiB    1 KiB   61 MiB  893 GiB  0.01   8.24    0      up  
 0    hdd  5.45699   1.00000  5.5 TiB   37 MiB  5.8 MiB    5 KiB   31 MiB  5.5 TiB     0   0.74    1      up  
 2    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
 5    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
 7    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
 9    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
11    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
12    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
14    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
16    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
18    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
20    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
22    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
24    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
26    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
29    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
31    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
33    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
35    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
37    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
39    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
41    ssd  0.87219   1.00000  893 GiB   32 MiB  5.1 MiB    6 KiB   27 MiB  893 GiB  0.00   3.99    0      up  
44    ssd  0.87219   1.00000  893 GiB   32 MiB  5.1 MiB    6 KiB   27 MiB  893 GiB  0.00   3.99    0      up  
 1    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
 3    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
 4    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
 6    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
 8    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
10    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
13    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
15    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
17    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
19    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
21    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
23    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
25    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
27    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
28    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
30    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
32    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
34    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
36    hdd  5.45699   1.00000  5.5 TiB   32 MiB  5.1 MiB    7 KiB   27 MiB  5.5 TiB     0   0.64    0      up  
38    hdd  5.45699   1.00000  5.5 TiB   37 MiB  5.8 MiB    6 KiB   31 MiB  5.5 TiB     0   0.74    1      up  
42    ssd  0.87219   1.00000  893 GiB   32 MiB  5.1 MiB    6 KiB   27 MiB  893 GiB  0.00   3.99    0      up  
45    ssd  0.87219   1.00000  893 GiB   32 MiB  5.1 MiB    6 KiB   27 MiB  893 GiB  0.00   3.99    0      up  
                       TOTAL  227 TiB  2.1 GiB  257 MiB  350 KiB  1.4 GiB  227 TiB     0  
MIN/MAX VAR: 0.64/53.64  STDDEV: 0.01
```

通过磁盘大小可以看出，41，42，44，45 是 SSD， 需要调整，我这里已经调整好了

再次检查 osd tree
```

[<REDACTED>@k8s-octarine-01 ~]$ kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph osd tree  
ID   CLASS  WEIGHT     TYPE NAME                 STATUS  REWEIGHT  PRI-AFF  
 -1         227.00134  root default  
 -7           1.74438      host k8s-octarine-01  
 40    ssd    0.87219          osd.40                up   1.00000  1.00000  
 43    ssd    0.87219          osd.43                up   1.00000  1.00000  
-16           1.74438      host k8s-octarine-02  
 46    ssd    0.87219          osd.46                up   1.00000  1.00000  
 47    ssd    0.87219          osd.47                up   1.00000  1.00000  
-13           1.74438      host k8s-octarine-03  
 48    ssd    0.87219          osd.48                up   1.00000  1.00000  
 49    ssd    0.87219          osd.49                up   1.00000  1.00000  
 -3         110.88409      host k8s-octarine-04  
  0    hdd    5.45699          osd.0                 up   1.00000  1.00000  
  2    hdd    5.45699          osd.2                 up   1.00000  1.00000  
  5    hdd    5.45699          osd.5                 up   1.00000  1.00000  
  7    hdd    5.45699          osd.7                 up   1.00000  1.00000  
  9    hdd    5.45699          osd.9                 up   1.00000  1.00000  
 11    hdd    5.45699          osd.11                up   1.00000  1.00000  
 12    hdd    5.45699          osd.12                up   1.00000  1.00000  
 14    hdd    5.45699          osd.14                up   1.00000  1.00000  
 16    hdd    5.45699          osd.16                up   1.00000  1.00000  
 18    hdd    5.45699          osd.18                up   1.00000  1.00000  
 20    hdd    5.45699          osd.20                up   1.00000  1.00000  
 22    hdd    5.45699          osd.22                up   1.00000  1.00000  
 24    hdd    5.45699          osd.24                up   1.00000  1.00000  
 26    hdd    5.45699          osd.26                up   1.00000  1.00000  
 29    hdd    5.45699          osd.29                up   1.00000  1.00000  
 31    hdd    5.45699          osd.31                up   1.00000  1.00000  
 33    hdd    5.45699          osd.33                up   1.00000  1.00000  
 35    hdd    5.45699          osd.35                up   1.00000  1.00000  
 37    hdd    5.45699          osd.37                up   1.00000  1.00000  
 39    hdd    5.45699          osd.39                up   1.00000  1.00000  
 41    ssd    0.87219          osd.41                up   1.00000  1.00000  
 44    ssd    0.87219          osd.44                up   1.00000  1.00000  
 -5         110.88409      host k8s-octarine-05  
  1    hdd    5.45699          osd.1                 up   1.00000  1.00000  
  3    hdd    5.45699          osd.3                 up   1.00000  1.00000  
  4    hdd    5.45699          osd.4                 up   1.00000  1.00000  
  6    hdd    5.45699          osd.6                 up   1.00000  1.00000  
  8    hdd    5.45699          osd.8                 up   1.00000  1.00000  
 10    hdd    5.45699          osd.10                up   1.00000  1.00000  
 13    hdd    5.45699          osd.13                up   1.00000  1.00000  
 15    hdd    5.45699          osd.15                up   1.00000  1.00000  
 17    hdd    5.45699          osd.17                up   1.00000  1.00000  
 19    hdd    5.45699          osd.19                up   1.00000  1.00000  
 21    hdd    5.45699          osd.21                up   1.00000  1.00000  
 23    hdd    5.45699          osd.23                up   1.00000  1.00000  
 25    hdd    5.45699          osd.25                up   1.00000  1.00000  
 27    hdd    5.45699          osd.27                up   1.00000  1.00000  
 28    hdd    5.45699          osd.28                up   1.00000  1.00000  
 30    hdd    5.45699          osd.30                up   1.00000  1.00000  
 32    hdd    5.45699          osd.32                up   1.00000  1.00000  
 34    hdd    5.45699          osd.34                up   1.00000  1.00000  
 36    hdd    5.45699          osd.36                up   1.00000  1.00000  
 38    hdd    5.45699          osd.38                up   1.00000  1.00000  
 42    ssd    0.87219          osd.42                up   1.00000  1.00000  
 45    ssd    0.87219          osd.45                up   1.00000  1.00000
```

嗯，意满离

## Rook-Ceph 配置变更记录（基于官方示例）

由于本次部署直接基于官方仓库进行（打包时保留了 git 历史），  
因此所有配置调整都可以通过 `git diff` 进行追溯。

下面整理了本次的主要变更记录，方便理解整体调整内容。

### 变更概览

主要调整如下：

  1. 1\. 允许控制平面节点调度 Ceph 相关组件（添加 tolerations）
  2. 2\. 将 `rbd/storageclass` 副本数从 3 降低为 2（适用于资源受限环境）
  3. 3\. 允许 CSI Provisioner 调度到 control-plane 节点
  4. 4\. 固定 toolbox 镜像版本为 v19.2.3

```

diff --git a/deploy/examples/cluster.yaml b/deploy/examples/cluster.yaml  
index f9820f384..8c5383473 100644  
--- a/deploy/examples/cluster.yaml  
+++ b/deploy/examples/cluster.yaml  
@@ -175,6 +175,14 @@ spec:  
   # To control where various services will be scheduled by kubernetes, use the placement configuration sections below.  
   # The example under 'all' would have all services scheduled on kubernetes nodes labeled with 'role=storage-node' and  
   # tolerate taints with a key of 'storage-node'.  
+  
+  placement:  
+    all:  
+      tolerations:  
+        - key: node-role.kubernetes.io/control-plane  
+          operator: Exists  
+          effect: NoSchedule  
+  
   # placement:  
   #   all:  
   #     nodeAffinity:  
diff --git a/deploy/examples/csi/rbd/storageclass.yaml b/deploy/examples/csi/rbd/storageclass.yaml  
index f810cf6ae..137f4afcc 100644  
--- a/deploy/examples/csi/rbd/storageclass.yaml  
+++ b/deploy/examples/csi/rbd/storageclass.yaml  
@@ -6,7 +6,7 @@ metadata:  
 spec:  
   failureDomain: host  
   replicated:  
-    size: 3  
+    size: 2  
     # Disallow setting pool with replica 1, this could lead to data loss without recovery.  
     # Make sure you're *ABSOLUTELY CERTAIN* that is what you want  
     requireSafeReplicaSize: true  
diff --git a/deploy/examples/operator.yaml b/deploy/examples/operator.yaml  
index 34a47d225..aee00ca32 100644  
--- a/deploy/examples/operator.yaml  
+++ b/deploy/examples/operator.yaml  
@@ -222,9 +222,9 @@ data:  
   # (Optional) CephCSI RBD provisioner tolerations list(if specified, overrides CSI_PROVISIONER_TOLERATIONS).  
   # Put here list of taints you want to tolerate in YAML format.  
   # CSI provisioner would be best to start on the same nodes as other ceph daemons.  
-  # CSI_RBD_PROVISIONER_TOLERATIONS: |  
-  #   - key: node.rook.io/rbd  
-  #     operator: Exists  
+  CSI_RBD_PROVISIONER_TOLERATIONS: |  
+    - key: node-role.kubernetes.io/control-plane  
+      operator: Exists  
   # (Optional) CephCSI RBD plugin NodeAffinity (if specified, overrides CSI_PLUGIN_NODE_AFFINITY).  
   # CSI_RBD_PLUGIN_NODE_AFFINITY: "role=rbd-node"  
   # (Optional) CephCSI RBD plugin tolerations list(if specified, overrides CSI_PLUGIN_TOLERATIONS).  
diff --git a/deploy/examples/toolbox.yaml b/deploy/examples/toolbox.yaml  
index 5559e064a..b4f60af68 100644  
--- a/deploy/examples/toolbox.yaml  
+++ b/deploy/examples/toolbox.yaml  
@@ -19,7 +19,7 @@ spec:  
       serviceAccountName: rook-ceph-default  
       containers:  
         - name: rook-ceph-tools  
-          image: quay.io/ceph/ceph:v19  
+          image: quay.io/ceph/ceph:v19.2.3  
           command:  
             - /bin/bash  
             - -c
```

`CSI_RBD_PROVISIONER_TOLERATIONS` 的调整是后续部署 CNPG 时踩的一个坑。

由于将 PostgreSQL 的 3 个 Pod 调度到了 control-plane 节点，  
而该节点默认带有 `NoSchedule` taint，如果 CSI Provisioner 没有对应的 tolerations，会导致其无法调度到该节点，从而出现 PVC 无法创建/绑定的问题。

## 启动 dashboard

参考 https://rook.io/docs/rook/latest/Storage-Configuration/Monitoring/ceph-dashboard/

Ceph Dashboard 是 Ceph 官方提供的 Web 管理界面，可以用于查看和管理 Ceph 集群状态。

通过 Dashboard，可以直观查看：

  * • 集群健康状态
  * • MON 仲裁状态
  * • MGR、OSD 等守护进程状态
  * • Pool 和 PG 状态
  * • Ceph 服务日志
  * • 集群性能指标

简单来说：

> Ceph Dashboard = Ceph 集群的可视化运维入口。

不过需要注意，Dashboard 并不是命令行工具的替代品，更多用于日常巡检、状态查看和问题定位。

贴一张当前的 Dashboard 截图

![](https://r2.jeanjan.kdns.fr/pictures/img-a355243f01.png)

  

### 开启 Dashboard

在 Rook-Ceph 中，Dashboard 的配置由 CephCluster CRD 管理。

默认情况下，Dashboard 功能已经开启：
```

spec:  
  dashboard:  
    enabled: true
```

看一下 svc
```

[<REDACTED>@k8s-octarine-01 ~]$ kubectl -n rook-ceph get svc  
  
NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE  
rook-ceph-exporter        ClusterIP   10.96.125.10    <none>        9926/TCP            25m  
rook-ceph-mgr             ClusterIP   10.96.166.75    <none>        9283/TCP            25m  
rook-ceph-mgr-dashboard   ClusterIP   10.96.100.156   <none>        8443/TCP            25m  
rook-ceph-mon-a           ClusterIP   10.96.109.113   <none>        6789/TCP,3300/TCP   31m  
rook-ceph-mon-b           ClusterIP   10.96.104.36    <none>        6789/TCP,3300/TCP   26m  
rook-ceph-mon-c           ClusterIP   10.96.179.131   <none>        6789/TCP,3300/TCP   26m
```

可以看到 `rook-ceph-mgr-dashboard` 已经创建，对外提供 HTTPS 服务，端口为 8443。

### 获取 Dashboard 登录密码

Rook 会自动创建 Dashboard 登录凭据，存放在 secret 中

获得密码
```

[<REDACTED>@k8s-octarine-01 ~]$ kubectl -n rook-ceph get secret rook-ceph-dashboard-password -o jsonpath="{.data.password}" | base64 --decode
```

用户名 admin

### 从 Kubernetes 集群外访问 Dashboard

默认情况下，Dashboard Service 类型为 ClusterIP，只能在 Kubernetes 集群内部访问。

如果需要从外部网络访问，需要额外暴露 Service。

参考 https://rook.io/docs/rook/latest/Storage-Configuration/Monitoring/ceph-dashboard/#viewing-the-dashboard-external-to-the-cluster

之前文章中已经部署了 MetalLB （参见[1.3-在 K8s 中部署 MetalLB：让裸机也拥有 LoadBalancer](https://mp.weixin.qq.com/s?__biz=MzYyNTE1OTE2Mg==&mid=2247483833&idx=1&sn=74d61fa7bdc3bbbaf0b3a774f06f7d27&scene=21#wechat_redirect) ），这是我们访问 svc 的高可用通道，因此这里直接使用 LoadBalancer 类型 Service，将 Dashboard 暴露出去。
```

# rook/deploy/examples/dashboard-external-https.yaml  
apiVersion: v1  
kind: Service  
metadata:  
  name: rook-ceph-mgr-dashboard-external-https  
  namespace: rook-ceph # namespace:cluster  
  annotations:  
    metallb.universe.tf/allow-shared-ip: "shared-ip"  
  labels:  
    app: rook-ceph-mgr  
    rook_cluster: rook-ceph # namespace:cluster  
spec:  
  ports:  
    - name: dashboard  
      port: 30774  
      protocol: TCP  
      targetPort: 8443  
  selector:  
    app: rook-ceph-mgr  
    mgr_role: active  
    rook_cluster: rook-ceph # namespace:cluster  
  sessionAffinity: None  
  type: LoadBalancer  
  loadBalancerSourceRanges:  
    - 192.168.54.0/24
```

这也是本文第一次介绍 MetalLB 在实际业务 Service 中的使用。

### MetalLB 配置说明

这里有两个配置需要额外说明。

  1. 1\. `allow-shared-ip`

```

annotations:  
  metallb.universe.tf/allow-shared-ip: "shared-ip"
```

该配置用于开启 MetalLB 的共享 IP 功能。

当前环境中 LoadBalancer 的 VIP 地址池中只有一个 IP，如果每个 Service 都申请独立 VIP，会出现 IP 地址无法分配的问题。

开启共享 IP 后，多个 Service 可以复用同一个 VIP，但需要通过不同端口进行区分。

  1. 2\. `loadBalancerSourceRanges`

```

loadBalancerSourceRanges:  
  - 192.168.54.0/24
```

该配置用于限制允许访问 LoadBalancer Service 的来源地址。

这里使用 CIDR 格式配置访问范围，可以避免 Dashboard 暴露给不需要访问的网络。

## 总结

这次部署最大的几个关键点：

  1. 1\. **Rook-Ceph 是“运行在 K8s 内”的存储，而不是外部系统**
  2. 2\. **调度问题本质是 taint + affinity + anti-affinity 的组合**
  3. 3\. **磁盘必须是“干净设备”，否则 OSD 不会创建**
  4. 4\. **某些情况下需要重启 operator 才能触发状态刷新**

整体来看，Rook-Ceph 的部署并不复杂，但**对 Kubernetes 调度机制和存储设备状态非常敏感** 。

## 后续

部署完成后，Rook-Ceph 的使用可以从两个维度展开：一是对外提供稳定的存储能力，二是对内保障集群的可观测性与可运维性。

### 1\. 存储使用：存储池与存储类

在完成集群部署后，下一步就是将 Ceph 能力真正提供给业务使用，包括：

  * • 基于不同的磁盘类型创建 **Pool（存储池）** ，定义数据副本数
  * • 基于 Pool 创建 **StorageClass** ，对接 Kubernetes
  * • 提供不同类型存储：
```
* • RBD（块存储，对应 PVC）
* • CephFS（共享文件系统）
* • Object（对象存储，S3 兼容）
```

通过 StorageClass，业务可以像使用普通 Kubernetes 存储一样动态申请 Ceph 存储，实现真正的云原生集成。

### 2\. 运维与监控：Dashboard 与性能管理

在稳定运行阶段，需要关注集群的可观测性与运维能力，包括：

  * • 集成监控体系：
```
* • Prometheus + Grafana （这个需要后续介绍了安装 VictoriaMetrics 集群后才会讲到）
* • 关注指标：
  * • 集群健康状态（HEALTH）
  * • IO 延迟（latency）
  * • 吞吐（throughput）
  * • PG 状态
```

  * • 日常运维能力：
```
* • OSD 扩缩容
* • 磁盘替换
* • 数据重平衡控制  
```

  


