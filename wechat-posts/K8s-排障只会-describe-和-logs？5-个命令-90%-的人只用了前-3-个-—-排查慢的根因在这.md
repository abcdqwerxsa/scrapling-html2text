# K8s 排障只会 describe 和 logs？5 个命令 90% 的人只用了前 3 个 — 排查慢的根因在这

**作者**: 不怕慢
**发布时间**: 2026-07-18 07:00
**原文链接**: https://mp.weixin.qq.com/s/Tj8Gtww1O5fg1oJx5fNE_Q

---

# K8s 排障只会 describe 和 logs？5 个命令 90% 的人只用了前 3 个 — 排查慢的根因在这

> 你有没有遇到过这种情况——Pod 起不来，`kubectl describe pod` 看了半天看不出问题，日志也查了，就是不知道哪根筋搭错了。折腾两小时后发现，**一条没注意过的命令，10 秒就定位了** 。

K8s 排障最怕的不是问题难，而是**你翻来覆去就在那 3 条命令里打转** ：`describe` → `logs` → `exec`，遇到复杂问题就卡住。

今天翻车系列 #11，聊 5 个排障命令，其中 2 个很多人没当回事。这几个命令排了我 80% 的疑难杂症。

> 📌 本文关键词：K8s 排障命令、Kubectl 调试、Pod 排查、运维排障

——◆——

## 1\. `kubectl events` — 最容易被忽略的排障入口

大多数人的排障流程是：`kubectl describe pod xxx` → 翻到 Events 段。

但 `describe` 只显示当前 Pod 的 Events，**而且只保留最近几分钟的** 。如果你排查的是"Pod 被 OOMKill 了然后重启了"，等你看的时候 Events 可能已经被 GC 了。

**更好用的方式：**

bash

# 全局看 Event，按时间排序

kubectl get events \--sort-by='.lastTimestamp'

  

# 只看 Warning 级别的

kubectl get events \--field-selector type=Warning

  

# 只看某个 Pod 相关的

kubectl get events \--field-selector involvedObject.name=<pod-name>

**翻车案例** ：有一次 Pod 反复 CrashLoopBackOff，`describe` 看到的是"Back-off restarting failed container"，没有具体原因。用 `kubectl events --sort-by='.lastTimestamp'` 一查，发现前面还有一个 `OOMKilled` 事件被刷掉了。原来是 JVM 内存限制设小了。

**核心价值** ：Events 是 K8s 自己记录的关键日志，**比 Pod 日志更早暴露问题** 。排障第一步先看 Events，而不是先去 `kubectl logs`。

——◆——

## 2\. `kubectl top` — 一看就知道资源吃没吃满

很多人遇到 Pod 慢或者节点卡，第一反应是"去监控看看"。但如果本地环境没有监控（测试集群、本地 Minikube、开发环境），怎么办？

bash

# 看节点资源

kubectl top node

  

# 看 Pod 资源

kubectl top pod

  

# 按 CPU 排序，找到最吃资源的 Pod

kubectl top pod -A \--sort-by='cpu' | tail -10

  

# 按内存排序

kubectl top pod -A \--sort-by='memory' | tail -10

**翻车案例** ：有一次集群响应慢，以为是网络问题，排查半天。`kubectl top node` 一看，一个节点 CPU 已经 95% 了，上面跑了 20 多个 Pod，其中一个日志采集 Pod 把 CPU 吃满了。**2 分钟定位，而不是 2 小时。**

**使用场景** ： 

• **节点 NotReady → 先看`top node` 是否资源耗尽**

• **Pod 响应慢 → 先看`top pod` 是否 CPU/Memory 限制太小**

• **集群整体卡 → 先看`top node` 找热点节点**

——◆——

## 3\. `kubectl debug` — 临时调一个排障容器

这个命令很多人知道但不常用。`kubectl debug` 可以在目标 Pod 旁边起一个排障容器，共享 network namespace、存储卷等。

**用法：**

bash

# 在目标 Pod 旁边起一个 debug 容器

kubectl debug -it <pod-name> \--image=busybox \--target=<container-name>

  

# 复制一个 Pod 来调试（不改原 Pod）

kubectl debug <pod-name> -it \--copy-to=<debug-pod-name> \--image=busybox

  

# 在节点上起排障 Pod

kubectl debug node/<node-name> -it \--image=busybox

**翻车案例** ：有一次 Pod 里没装 `curl` 和 `netstat`，连不上 Service。用 `kubectl debug` 起一个 busybox 容器共享网络空间，`curl http://service-name:port` 发现 DNS 解析不了——原来是 CoreDNS 的 ConfigMap 配错了。**不用改 Pod，不用重启，直接在旁边调试。**

**为什么这个好用** ：生产环境的 Pod 镜像通常最小化，没有排障工具。`kubectl debug` 让你在不改 Pod 定义的前提下，拿一个全工具容器去帮忙看问题。

——◆——

## 4\. `kubectl auth can-i` — 5 秒确认权限问题

RBAC 导致的 403 错误，我见过太多人排查方式就是"翻 YAML 看 Role 和 RoleBinding"。但 RBAC 规则一多，人工核对就是**眼睛看花、越看越晕** 。

bash

# 检查当前用户能否创建 Deployment

kubectl auth can-i create deployments

  

# 检查某个 ServiceAccount 能否 get Pod

kubectl auth can-i get pods \--as=system:serviceaccount:<ns>:<sa-name>

  

# 检查能不能访问某个资源

kubectl auth can-i list pods \--all-namespaces

  

# 带 Verb 和 SubResource 检查

kubectl auth can-i get pods/log

**翻车案例** ：CI/CD 流水线报 403，排查了 2 小时 YAML，最后用 `kubectl auth can-i create deployments --as=system:serviceaccount:ci:deployer` 一测，发现绑定的 Role 只有 `get` 权限，没有 `create`。**5 秒确认，不用翻 YAML。**

**使用场景** ： 

• **CI/CD 报 403 → 用`--as` 模拟 ServiceAccount 检查**

• **应用报 Forbidden → 确认 Pod 绑定的 ServiceAccount 是否有对应权限**

• **权限审计 → 批量检查关键操作的权限**

——◆——

## 5\. `kubectl rollout` — 回滚和状态检查

很多人部署完了发现有问题，第一反应是手动改 YAML 再 apply。但更标准的做法是用 `rollout`。

bash

# 查看 rollout 历史

kubectl rollout history deployment/<deploy-name>

  

# 回滚到上一个版本

kubectl rollout undo deployment/<deploy-name>

  

# 回滚到指定版本

kubectl rollout undo deployment/<deploy-name> \--to-revision=3

  

# 查看 rollout 状态

kubectl rollout status deployment/<deploy-name>

**翻车案例** ：有一次更新 ConfigMap 后 Deployment 没更新（经典翻车），有人直接 `kubectl delete pod` 手动重启。但更稳妥的方式是：

bash

kubectl rollout restart deployment/<deploy-name>

这样 Deployment Controller 会按 `maxUnavailable` 和 `maxSurge` 策略优雅滚动重启，**不会造成服务中断** 。

——◆——

## 排障命令速查表

| 命令                   | 场景              | 一句话说明                  |
|----------------------|-----------------|------------------------|
| `kubectl events`     | 任何问题第一步         | 看 K8s 自己记录的异常事件        |
| `kubectl top`        | 怀疑资源不足          | 看一眼 CPU/Memory 就知道     |
| `kubectl debug`      | Pod 里没有排障工具     | 在旁边起一个全工具容器            |
| `kubectl auth can-i` | 报 403 Forbidden | 5 秒确认权限问题              |
| `kubectl rollout`    | 部署出问题想回滚        | 比手动 delete pod 安全 10 倍 |

——◆——

## 延伸总结

这几个命令的价值不在于"多厉害"，而在于**帮你从死胡同里跳出来** 。

• **看了半天 Pod 日志看不出问题？→ 先看`events`，K8s 自己可能已经告诉你了**

• **怀疑资源问题但没有监控？→`top` 看一眼**

• **Pod 镜像没有排障工具？→`debug` 起一个**

• **权限报错翻 YAML 头晕？→`auth can-i` 5 秒确认**

• **部署搞砸了不知道怎么办？→`rollout undo` 一键回滚**

**记住一句话：排障不是比谁命令多，而是比谁能更快找到根因。**

——◆——

> 💡 这 5 个命令里，你平时用了几个？有没有遇到"一条命令救了一命"的场景？评论区聊聊👇

觉得有用？转发给被 K8s 坑过的同事，少走弯路。

📖 **延伸阅读（历史翻车系列）：**

• **K8s 翻车系列 #10：K8s ConfigMap 更新了，Pod 还在用旧配置：排查 4 小时才发现是这 3 个坑 — 直接复制修复**

• **K8s 翻车系列 #9：K8s 证书过期，整个集群挂了：kubeadm 证书续期全流程 — 附生产执行清单**

