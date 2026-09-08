# KServe + HAMi：一张 GPU 如何运行多个推理服务

**作者**: 探索云原生
**发布时间**: 2026-08-11 08:00
**原文链接**: https://mp.weixin.qq.com/s/az84N9HFcMsvKpDtToDIVQ

---

  

![HAMi GPU 共享：KServe 原生 DRA 实战](https://r2.jeanjan.kdns.fr/pictures/img-3df6e7cc01.jpeg)HAMi GPU 共享：KServe 原生 DRA 实战

前面已经用 KServe 跑起了 Qwen，但一个小模型独占一张 GPU 有些浪费。这篇则是在此基础上引入 HAMi，通过 HAMi 实现 GPU 共享，让多个小模型共用一张 GPU。

## 准备环境

本次测试环境如下：
```

Kubernetes v1.36.1  
KServe v0.18.0  
HAMi 0.2.1  
HAMi NVIDIA DRA Driver v0.1.0  
containerd 2.2.4  
NVIDIA Driver 580.173.02  
Tesla T4 15 GiB x 1  

```

本文从 HAMi 安装和原生 DRA 资源声明开始，完整走通 KServe 集成 HAMi GPU 共享部分。

  * KServe 环境安装方式沿用[一个 Deployment 就能跑 vLLM，为什么还需要 KServe？](https://mp.weixin.qq.com/s?__biz=Mzk0NzE5OTQyOQ==&mid=2247489919&idx=1&sn=79b0636cc2b9d4c2467f5d9b197c147f&scene=21#wechat_redirect)中的步骤。
  * HAMi 的使用可以参考[Kubernetes GPU 虚拟化实战：HAMi DRA 模式完整指南](https://mp.weixin.qq.com/s?__biz=Mzk0NzE5OTQyOQ==&mid=2247489755&idx=1&sn=b04885ddce76aeb5b0dedf1135a053ff&scene=21#wechat_redirect)。

### 安装 GPU Operator

由 GPU Operator 安装 NVIDIA Driver、Container Toolkit 和监控组件，但关闭原生 NVIDIA Device Plugin，后续由 HAMi DRA Driver 管理 GPU：
```

helm repo add nvidia https://helm.ngc.nvidia.com/nvidia  
helm repo update  
  
helm upgrade --install gpu-operator nvidia/gpu-operator \  
  -n gpu-operator --create-namespace \  
  --version=v26.3.1 \  
  --set driver.enabled=true \  
  --set devicePlugin.enabled=false \  
  --wait  

```

如果节点已经预装 NVIDIA Driver，可以把 `driver.enabled` 改为 `false`。无论驱动由谁安装，`devicePlugin.enabled=false` 都不能省略，否则原生 Device Plugin 和 HAMi-DRA 会同时管理同一设备。

### 安装 cert-manager

HAMi-DRA Webhook 需要 TLS 证书，测试环境使用 cert-manager 签发：
```

helm repo add cert-manager https://charts.jetstack.io  
helm repo update  
  
helm upgrade --install cert-manager cert-manager/cert-manager \  
  -n cert-manager --create-namespace \  
  --set crds.enabled=true \  
  --wait  

```

### 安装 HAMi-DRA

为需要接管的 GPU 节点添加 `gpu=on` 标签，再安装本文实测的 HAMi-DRA 0.2.1：
```

helm repo add hami-dra https://project-hami.github.io/HAMi-DRA/  
helm repo update  
  
GPU_NODE=lixd-test-gpu  # 替换为实际 GPU 节点名  
kubectl label node "$GPU_NODE" gpu=on  
  
helm upgrade --install hami-dra hami-dra/hami-dra \  
  -n hami-dra \  
  --create-namespace \  
  --version 0.2.1 \  
  --wait  

```

上面的命令适用于 GPU Operator 安装 Driver 的场景。如果 NVIDIA Driver 由宿主机预装，则增加：
```

--set drivers.nvidia.containerDriver=false  

```

### 确认 GPU 共享容量

安装完成后，HAMi 创建了一个 DeviceClass：
```

root@lixd-test-gpu:~# kubectl get deviceclass  
NAME                            AGE  
hami-core-gpu.project-hami.io   3d4h  

```

同时节点插件通过 ResourceSlice 发布 GPU 信息：
```

kubectl get resourceslice -o yaml  

```

输出中只保留本文关心的字段：
```

spec:  
  driver: hami-core-gpu.project-hami.io  
  nodeName: lixd-test-gpu  
  devices:  
  - name: hami-gpu-0  
    allowMultipleAllocations: true  
    attributes:  
      productName:  
        string: Tesla T4  
      type:  
        string: hami-gpu  
    capacity:  
      cores:  
        value: "100"  
      memory:  
        value: 15Gi  

```

`allowMultipleAllocations: true` 表示同一个设备可以接受多份分配。这里的 `memory` 和 `cores` 是 HAMi 用于调度和限制的可消耗容量，不是 Node 上的传统扩展资源。

## 创建共享 GPU 推理服务

KServe 0.18 版本已经支持原生 DRA，可以在 Predictor 级引用 `ResourceClaimTemplate`，再由容器级 `resources.claims` 使用对应的 Claim。

我们只需要提前创建一个 ResourceClaimTemplate，然后在 InferenceService 中引用即可，完整的 YAML 如下：
```

cat <<'EOF' > qwen-llm-hami.yaml  
apiVersion: resource.k8s.io/v1  
kind: ResourceClaimTemplate  
metadata:  
  name: qwen-hami-gpu  
  namespace: kserve-test  
spec:  
  spec:  
    devices:  
      requests:  
        - name: gpu  
          exactly:  
            deviceClassName: hami-core-gpu.project-hami.io  
            allocationMode: ExactCount  
            count: 1  
            capacity:  
              requests:  
                memory: 3Gi  
                cores: "20"  
---  
apiVersion: serving.kserve.io/v1beta1  
kind: InferenceService  
metadata:  
  name: qwen-llm  
  namespace: kserve-test  
  annotations:  
    serving.kserve.io/deploymentMode: Standard  
spec:  
  predictor:  
    minReplicas: 2  
    resourceClaims:  
      - name: gpu  
        resourceClaimTemplateName: qwen-hami-gpu  
    model:  
      modelFormat:  
        name: huggingface  
      image: docker.m.daocloud.io/kserve/huggingfaceserver:v0.18.0-gpu  
      storageUri: pvc://qwen-model  
      args:  
        - --model_name=qwen  
        - --max_model_len=4096  
        - --max-num-seqs=32  
        - --gpu-memory-utilization=0.8  
      resources:  
        requests:  
          cpu: "1"  
          memory: 4Gi  
        limits:  
          cpu: "2"  
          memory: 6Gi  
        claims:  
          - name: gpu  
EOF  
  
kubectl apply -f qwen-llm-hami.yaml  
  
kubectl wait --for=condition=Ready \  
  inferenceservice/qwen-llm -n kserve-test --timeout=10m  

```

`minReplicas: 2` 保证 Demo 期间至少存在两个 Predictor，用于验证它们能否同时获得共享 GPU 配额，不展开副本自动调整行为。

这里没有再声明 `nvidia.com/gpu`、`nvidia.com/gpumem` 或 `nvidia.com/gpucores`。CPU 和内存仍使用普通 requests/limits，GPU 完全使用 DRA Claim 形式声明。

![](https://r2.jeanjan.kdns.fr/pictures/img-3df6e7cc02.png)原生 DRA 通过 ResourceClaim 分配共享 GPU

### 确认 KServe 写入 DRA 引用

KServe 的 HuggingFace Runtime 原本根据 GPU limit 选择 `-gpu` 镜像。原生 DRA 配置里没有这个 limit，因此本文显式指定已经验证过的 GPU 镜像。`docker.m.daocloud.io` 是测试环境使用的镜像代理；如果环境可以直接访问 Docker Hub，可以改为 `kserve/huggingfaceserver:v0.18.0-gpu`。

KServe 最终生成的 Deployment 保留了两级引用：
```

kubectl get deployment -n kserve-test \  
  -l serving.kserve.io/inferenceservice=qwen-llm -o yaml  

spec:  
  resourceClaims:  
    - name: gpu  
      resourceClaimTemplateName: qwen-hami-gpu  
  containers:  
    - name: kserve-container  
      resources:  
        claims:  
          - name: gpu  

```

Deployment 创建两个 Pod 后，Kubernetes 会根据同一个 ResourceClaimTemplate 为每个 Pod 生成独立 Claim。不能让多个副本直接引用一份固定 ResourceClaim，否则它们不会获得各自独立的 3Gi/20 配额。

## 验证 DRA 容量分配

### 查看 ResourceClaim 的申请与分配

Kubernetes 为每个 Pod 生成一份 Claim。下面只保留其中一份 Claim 的申请字段；它由 Pod 持有，Pod 删除后会一起清理：
```

CLAIM=$(kubectl get resourceclaim -n kserve-test -o name | head -n 1)  
kubectl get -n kserve-test "$CLAIM" -o yaml  

apiVersion: resource.k8s.io/v1  
kind: ResourceClaim  
spec:  
  devices:  
    requests:  
      - name: gpu  
        exactly:  
          allocationMode: ExactCount  
          count: 1  
          deviceClassName: hami-core-gpu.project-hami.io  
          capacity:  
            requests:  
              memory: 3Gi  
              cores: "20"  

```

调度完成后，Claim 状态中的关键字段记录了实际分配：
```

status:  
  allocation:  
    devices:  
      results:  
        - device: hami-gpu-0  
          driver: hami-core-gpu.project-hami.io  
          consumedCapacity:  
            memory: 3Gi  
            cores: "20"  

```

ResourceClaimTemplate 只定义申请规格，Kubernetes 为每个 Pod 生成 Claim，并完成设备选择和容量扣减。HAMi DRA Driver 随后响应 kubelet 的 `NodePrepareResources`，生成 CDI 配置并返回设备信息，最终由 containerd 把对应 GPU 和 HAMi-Core 运行环境应用到容器。

### 查看容器内的显存限制

进入其中一个 Predictor 容器执行完整的 `nvidia-smi`：
```

POD=$(kubectl get pod -n kserve-test \  
  -l serving.kserve.io/inferenceservice=qwen-llm \  
  -o name | head -n 1)  
  
kubectl exec -n kserve-test "$POD" -- nvidia-smi  

```

可以看到 HAMi 把同一张 GPU 的可见显存限制为 3072 MiB。下面是本次实测的完整状态表；命令前后的 HAMI 初始化和退出日志不属于 `nvidia-smi` 输出，这里没有混入：
```

Thu Aug  6 03:46:03 2026  
+-----------------------------------------------------------------------------------------+  
| NVIDIA-SMI 580.173.02             Driver Version: 580.173.02     CUDA Version: 13.0     |  
+-----------------------------------------+------------------------+----------------------+  
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |  
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |  
|                                         |                        |               MIG M. |  
|=========================================+========================+======================|  
|   0  Tesla T4                       Off |   00000000:00:06.0 Off |                    0 |  
| N/A   44C    P0             28W /   70W |    3015MiB /   3072MiB |      0%      Default |  
|                                         |                        |                  N/A |  
+-----------------------------------------+------------------------+----------------------+  
  
+-----------------------------------------------------------------------------------------+  
| Processes:                                                                              |  
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |  
|        ID   ID                                                               Usage      |  
|=========================================================================================|  
|  No running processes found                                                             |  
+-----------------------------------------------------------------------------------------+  

```

## 验证两个副本共享同一张 GPU

### 检查 Pod 和 Claim

把 Predictor 的最小副本数设为 2，两份 Pod 使用相同的 3Gi、`cores=20` 配置。

![整卡分配与 HAMi-DRA 共享对比](https://r2.jeanjan.kdns.fr/pictures/img-3df6e7cc04.jpeg)整卡分配与 HAMi-DRA 共享对比

先查看 Pod 和 Claim：
```

kubectl get pod -n kserve-test \  
  -l serving.kserve.io/inferenceservice=qwen-llm -o wide  
  
kubectl get resourceclaim -n kserve-test  
  
for claim in $(kubectl get resourceclaim -n kserve-test -o name); do  
  kubectl get -n kserve-test "$claim" \  
    -o jsonpath='{.metadata.name}{" device="}{.status.allocation.devices.results[0].device}{" memory="}{.status.allocation.devices.results[0].consumedCapacity.memory}{" cores="}{.status.allocation.devices.results[0].consumedCapacity.cores}{"\n"}'  
done  

```

本次新建的两份 Claim 都分配成功：
```

NAME                                           STATE                AGE  
qwen-llm-predictor-544cc75b4-7fvcc-gpu-g8b6c   allocated,reserved   3m3s  
qwen-llm-predictor-544cc75b4-fz5hq-gpu-9lxw2   allocated,reserved   2m48s  
  
qwen-llm-predictor-544cc75b4-7fvcc-gpu-g8b6c device=hami-gpu-0 memory=3Gi cores=20  
qwen-llm-predictor-544cc75b4-fz5hq-gpu-9lxw2 device=hami-gpu-0 memory=3Gi cores=20  

```

两个 Pod 都调度到 `lixd-test-gpu`，并分别看到 3072 MiB 显存：
```

NAME                                 READY   STATUS    RESTARTS   AGE     IP              NODE            NOMINATED NODE   READINESS GATES  
qwen-llm-predictor-544cc75b4-7fvcc   1/1     Running   0          3m3s    172.25.118.13   lixd-test-gpu   <none>           <none>  
qwen-llm-predictor-544cc75b4-fz5hq   1/1     Running   0          2m48s   172.25.118.3    lixd-test-gpu   <none>           <none>  

```

### 检查两个容器的可见显存

逐个进入容器检查可见 GPU：
```

for pod in $(kubectl get pod -n kserve-test \  
  -l serving.kserve.io/inferenceservice=qwen-llm -o name); do  
  kubectl exec -n kserve-test "$pod" -- \  
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader  
done  

```

两个容器都返回：
```

Tesla T4, 3072 MiB  
Tesla T4, 3072 MiB  

```

### 发起推理请求

通过 Gateway 调用接口：
```

ENVOY_SERVICE=$(kubectl get service -n envoy-gateway-system \  
  -l gateway.envoyproxy.io/owning-gateway-name=kserve-ingress-gateway \  
  -o jsonpath='{.items[0].metadata.name}')  
  
NODE_PORT=$(kubectl get service -n envoy-gateway-system "$ENVOY_SERVICE" \  
  -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}')  
  
NODE_IP=$(kubectl get node \  
  -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')  
  
GATEWAY_ADDR="${NODE_IP}:${NODE_PORT}"  
  
curl -H 'Host: qwen-llm-kserve-test.example.com' \  
  -H 'Content-Type: application/json' \  
  "http://${GATEWAY_ADDR}/openai/v1/chat/completions" \  
  -d '{  
    "model": "qwen",  
    "messages": [{"role": "user", "content": "Answer only with the number: 2+3"}],  
    "max_tokens": 8,  
    "temperature": 0  
  }'  

```

API 可以正常返回，说明在使用 GPU 共享之后，服务依旧可以正常运行。

## 清理资源

验证完成后删除 InferenceService 和 ResourceClaimTemplate：
```

kubectl delete inferenceservice qwen-llm -n kserve-test  
kubectl delete resourceclaimtemplate qwen-hami-gpu -n kserve-test  

```

两份由 Pod 生成的 ResourceClaim 会随 Pod 一起删除。

## 总结

KServe 可以直接通过 `ResourceClaimTemplate` 和 `resources.claims` 使用 HAMi DRA 模式，不需要额外适配。每个 Predictor Pod 都会生成一份独立 ResourceClaim，再由 HAMi 分配显存和算力配额。

通过 HAMi 共享后，一张 GPU 可以同时承载多个推理副本或服务工作负载，避免小模型整卡独占，让空闲的显存和算力得到更充分的利用。

  

  

![](https://r2.jeanjan.kdns.fr/pictures/img-3df6e7cc05.gif)  
  
  
往期回顾

  

[一个 Deployment 就能跑 vLLM，为什么还需要 KServe？](https://mp.weixin.qq.com/s?__biz=Mzk0NzE5OTQyOQ==&mid=2247489919&idx=1&sn=79b0636cc2b9d4c2467f5d9b197c147f&scene=21#wechat_redirect)

  

[Kubernetes 官方出品：一个 Controller 搞定 Job 排队和资源配额](https://mp.weixin.qq.com/s?__biz=Mzk0NzE5OTQyOQ==&mid=2247489879&idx=1&sn=6bd425a8a5047149122a74fe299392da&scene=21#wechat_redirect)

  

[K8s 1.36 ImageVolume GA：OCI 镜像不再只能跑容器](https://mp.weixin.qq.com/s?__biz=Mzk0NzE5OTQyOQ==&mid=2247489872&idx=1&sn=08f02faa32fabc8f836e99586eebeb56&scene=21#wechat_redirect)

  

[OpenSpec + Superpowers: SDD+TDD 双驱动 AI 编程工作流](https://mp.weixin.qq.com/s?__biz=Mzk0NzE5OTQyOQ==&mid=2247489845&idx=1&sn=8c0e13ced3209f41bf9b4001c6434942&scene=21#wechat_redirect)

  

  

  
![](https://r2.jeanjan.kdns.fr/pictures/img-3df6e7cc06.gif)  

🙏 感谢阅读！

如果本文对你有帮助，欢迎：  
👍 点赞 | 👀 在看 | 🔁 转发

✨ 想第一时间收到推送？  
记得给「**探索云原生** 」加上 星标 ⭐ 或点个关注！

  

我们下期再见！

  

  
![](https://r2.jeanjan.kdns.fr/pictures/img-3df6e7cc07.gif)  

  

  


