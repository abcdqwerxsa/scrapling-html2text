# Kubernetes NodePort 获取真实客户端 IP 实践：externalTrafficPolicy Local 与 Cluster 深度对比

**作者**: 悉数洞鉴
**发布时间**: 2026-08-05 08:00
**原文链接**: https://mp.weixin.qq.com/s/N2nVHHbbhOwFVaULzJ2vdw

---

第一次用 NodePort 把服务暴露到集群外时，在 Pod 里记访问日志，发现记下来的客户端 IP 全是 Node 的 IP，不是真正的访客。查了半天才弄明白，问题不在代码，在 NodePort 自己身上。要看清怎么回事，得跟着一个包从客户端到 Pod 再回来，走一遍。

客户端 C 访问 Node1 的 30000 端口，但真正处理请求的那个 Pod，跑在 Node2 上。这是 NodePort 再正常不过的情况——你访问任意一台节点的端口，流量最后都会被转到有 Pod 的那台节点。

Node1 收到包之后，得知道往哪送。kube-proxy 在 Node1 上装了一条 DNAT 规则，把目的地址从 Node1:30000 改写成 Pod 的真实地址 PodIP:8080，然后把包从 Node1 发到 Node2 上的 Pod。

到这儿都没问题。麻烦出在 Pod 回包的时候。

## 为什么 Pod 不能直接回给客户端

Pod 拿到包，看了一眼 IP 头里的源地址，是 C（客户端）。它很自然地，把响应发回给 C。

但客户端这边不认这个包。客户端当初建连接的时候，对端是 Node1:30000。现在它突然收到一个来自 PodIP:8080 的包——源地址、源端口全变了，五元组对不上——操作系统直接把这个包丢掉，连接就卡住了。

这里有个死结：Pod 必须回给客户端，但客户端只认 Node1 发来的包。

## SNAT 就是解开这个死结的

办法是让 Pod 以为对端不是客户端 C，而是 Node1。

Node1 在转发之前，除了改目的地址（DNAT），顺手把源地址也改掉，改成自己的 IP。这样 Pod 看到的源地址是 Node1，回包就先回到 Node1。Node1 收到回包，再把源地址换回 Node1:30000、目的地址换回 C，发给客户端。客户端一看，是我连的那个 Node 回的包，收下。

Node1 之所以能把回包正确还原，是因为当初做 DNAT+SNAT 时，conntrack（连接跟踪）已经记下了这条连接的五元组映射表。Pod 的回包到达 Node1 时，内核照着这张表逆向做转换，源地址才被改回 Node1:30000。没有这张表，Node1 根本不知道该把回包伪装成谁发来的。

这一步改源地址的动作，就叫 SNAT。Kubernetes 把它放在 NodePort 的默认行为里，因为只要发生跨节点转发，就绕不开它。

![](https://r2.jeanjan.kdns.fr/pictures/img-d390187901.png)

## 看看 kube-proxy 到底写了什么

光讲道理不够，看 kube-proxy 在 iptables 里到底塞了什么。默认 iptables 模式下，NodePort 流量从 PREROUTING 进来，跳到 KUBE-NODEPORTS 链（由 KUBE-SERVICES 跳转而来），按端口匹配到对应的 KUBE-SVC-，再跳到 KUBE-SEP- 做 DNAT。想自己看，在节点上跑：
```

iptables -t nat -L KUBE-SERVICES -n --line-numbers | grep 30000
```

默认 externalTrafficPolicy（也就是 Cluster）下，这条链里会先经过一条 KUBE-MARK-MASQ，把包打上一个 0x4000 的标记，最后在 KUBE-POSTROUTING 统一做 MASQUERADE。把每次都会变的哈希后缀去掉，结构是这样的：
```

-A KUBE-SVC-xxxx -j KUBE-MARK-MASQ  
-A KUBE-SVC-xxxx -j KUBE-SEP-xxxx  
-A KUBE-SEP-xxxx -p tcp -j DNAT --to-destination POD_IP:8080  
-A KUBE-POSTROUTING -m mark --mark 0x4000/0x4000 -j MASQUERADE
```

KUBE-MARK-MASQ 那条就是 SNAT 的开关：它只在需要跨节点转发时给包打标记（Local 模式下流量不跨节点，内核不会匹配到这条规则），真正改写源地址是在 POSTROUTING 阶段做的。

## 代价是 Pod 看不见真实 IP

SNAT 一开，Pod 里读到的源地址永远是这个 Node 的 IP，不是真正的客户端。如果你的服务要靠真实 IP 做地域封禁、访问审计、按 IP 限流，这个代价你不能忽视——你眼里看到的"客户端"，其实全是集群内部的节点。

## 想要真实 IP，开 Local 模式

kube-proxy 给了一个开关：externalTrafficPolicy: Local。开了之后，NodePort 流量只会转发给本节点上的 Pod，不做跨节点转发，也就不需要 SNAT。因为 Pod 和进来的网卡在同一台机器，Pod 回包直接发回客户端就行，中间没有"第二台机器"需要去伪装。

服务定义里就这么一行：
```

spec:  
  type: NodePort  
  externalTrafficPolicy: Local
```

Local 模式下，KUBE-SVC 链不再经过 KUBE-MARK-MASQ，也就没有 0x4000 标记，POSTROUTING 自然不会对它做 MASQUERADE。结果就是 Pod 拿到的源地址，原封不动是客户端的真实 IP。

![](https://r2.jeanjan.kdns.fr/pictures/img-d390187902.png)

## 但 Local 把问题推到了别处

Local 的语义很硬：流量只在本机处理。这就带来一个副作用——如果前端的负载均衡（比如云厂商的 SLB）把请求送到了一个没有目标 Pod 的节点，这个节点既不做 DNAT 也不转发，直接把包丢了。表现出来就是一部分请求稳定超时，而且只在特定节点上出现。

这不是 SNAT 的问题，是 Local 模式为了保住真实 IP 必须付出的代价。

![](https://r2.jeanjan.kdns.fr/pictures/img-d390187903.png)

## 到底怎么配

不关心真实客户端 IP 的纯后端 API，Cluster 模式（默认）就够了，跨节点和高可用都帮你管好了，什么都不用动。

需要真实 IP（比如要记访客 IP、做源 IP 封禁），就上 Local 模式，但得把 Pod 分布和前端负载均衡一起配齐，否则就是拿可用性换可见性。两个能直接落地的配法：

第一个，用 DaemonSet 部署，保证每个节点都至少有一个 Pod 副本，这样任何节点收到请求都有本地 Pod 接。

第二个，让前端负载均衡只把流量送给有 Pod 的节点。像阿里云 SLB 配合 Local 模式时，后端健康检测会跳过那些没有 Pod 的节点，请求根本不会落到空节点上。

调试时最快的一个检查点：kubectl get svc <名字> -o yaml 看一眼 externalTrafficPolicy 字段。Pod 里 IP 不对，十次里有八次，就是它默认是 Cluster、做了 SNAT。

