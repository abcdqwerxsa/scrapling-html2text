# Prometheus实战：自定义指标采集与告警规则配置

**作者**: 玥哲
**发布时间**: 2026-07-15 09:01
**原文链接**: https://mp.weixin.qq.com/s/ESFRF3zX00209qYoAMeB6A

---

> 本文是「从零开始学 Kubernetes」系列第 **24** 篇，模块六 · K8s 可观测性的第二篇。

## 一、从"看别人的仪表盘"到"造自己的"

kube-prometheus-stack 一键部署后，Grafana 上的 Dashboard 很漂亮，但全是 K8s 自身的指标——节点 CPU、Pod 重启、Deployment 副本数。**你的业务指标呢？API 延迟、订单量、用户在线数？**

打个比方：K8s 自带监控就像汽车仪表盘——速度、油量、温度都有了。想知道"今天拉了多少乘客"？得自己装打车终端。**Prometheus 给你标准接口，代码得你自己写。**

本篇解决五个核心问题：

| 问题                      | 解答                   |
|-------------------------|----------------------|
| 业务代码怎么暴露指标？             | Java / Python 实战     |
| 暴露后怎么让 Prometheus 自动采集？ | ServiceMonitor 完整配置  |
| 采集到的数据怎么查？              | PromQL 四维度查询         |
| 怎么变成告警？                 | PrometheusRule 设计到上线 |
| 生产环境有哪些坑？               | 高基数标签、内存爆炸、告警风暴      |

## 二、应用暴露 Prometheus 指标

### 2.1 基本原理

Prometheus 用 **HTTP GET 拉取`/metrics` 端点**，解析文本格式数据：

# HELP http_requests_total Total number of HTTP requests # TYPE http_requests_total counter http_requests_total{method="GET",status="200"} 1027 http_requests_total{method="POST",status="500"} 3

格式很简单：`# HELP` 说明 → `# TYPE` 类型（counter/gauge/histogram/summary）→ 指标名{标签} 数值。各语言有现成的客户端库，不用手写文本。

### 2.2 Spring Boot (Java)：零代码暴露指标

Spring Boot 通过 **Micrometer** 对接 Prometheus，几乎不用写代码，框架自动暴露几十个指标。

**添加依赖** （pom.xml）：

<dependency> <groupId>org.springframework.boot</groupId> <artifactId>spring-boot-starter-actuator</artifactId> </dependency> <dependency> <groupId>io.micrometer</groupId> <artifactId>micrometer-registry-prometheus</artifactId> </dependency>

**配置 application.yml** ：

management: endpoints: web: exposure: include: health,prometheus,metrics metrics: tags: application: order-service distribution: percentiles-histogram: http.server.requests: true percentiles: http.server.requests: 0.5, 0.95, 0.99

一行 Java 代码没写，你就有：HTTP 请求 QPS + 延迟分布（P50/P95/P99）、JVM 内存/GC/线程、进程 CPU、数据库连接池。

**自定义业务指标** ——统计订单量和处理耗时：

@Component public class OrderMetrics { private final Counter orderCreatedCounter; private final Counter orderFailedCounter; private final Timer orderProcessTimer; public OrderMetrics(MeterRegistry registry) { this.orderCreatedCounter = Counter.builder("order_created_total") .description("Total orders created") .register(registry); this.orderFailedCounter = Counter.builder("order_failed_total") .description("Total failed orders") .register(registry); this.orderProcessTimer = Timer.builder("order_process_duration") .publishPercentiles(0.5, 0.95, 0.99) .register(registry); } }

> **💡** **Micrometer 是"监控界的 SLF4J"** ——一套 API 对接多个监控系统（Prometheus、Datadog、New Relic），换系统业务代码不用改。 

### 2.3 Python (FastAPI)：轻量直接

pip install fastapi uvicorn prometheus-clientfrom prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST from fastapi import FastAPI, Request, Response app = FastAPI() REQUESTS = Counter('http_requests_total', 'Total requests', ['method', 'path', 'status']) REQUEST_LATENCY = Histogram('request_duration_seconds', 'Latency', ['method', 'path']) IN_PROGRESS = Gauge('in_progress_requests', 'In-flight requests') @app.middleware("http") async def metrics_middleware(request: Request, call_next): IN_PROGRESS.inc() start = time.time() try: response = await call_next(request) status = response.status_code except Exception: status = 500 raise finally: IN_PROGRESS.dec() latency = time.time() - start REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(latency) REQUESTS.labels(method=request.method, path=request.url.path, status=str(status)).inc() return response @app.get("/metrics") def get_metrics(): return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

> **⚠️** **高基数标签陷阱** ：如果路由是 `/api/orders/{order_id}`，每个不同 ID 会产生独立标签值，导致时间序列爆炸。**用路由模板替代实际路径** 。

### 2.4 四种指标类型速查

| 类型            | 特点      | 用途                    |
|---------------|---------|-----------------------|
| **Counter**   | 只增不减    | 请求总数、错误总数、订单量         |
| **Gauge**     | 可增可减    | CPU 使用率、内存、活跃连接数      |
| **Histogram** | 桶分布     | 延迟分布（计算 P50/P95/P99）  |
| **Summary**   | 客户端计算分位 | 类似 Histogram，但算分位在客户端 |

## 三、ServiceMonitor：声明式采集配置

应用暴露了 `/metrics`，下一步告诉 Prometheus 去采集它。

### 3.1 ServiceMonitor 配置

apiVersion: monitoring.coreos.com/v1 kind: ServiceMonitor metadata: name: order-service namespace: production labels: release: kube-prometheus-stack # ⚠️ 必须匹配 Prometheus selector spec: selector: matchLabels: app: order-service namespaceSelector: matchNames: [production] endpoints: \- port: metrics path: /metrics interval: 30s scrapeTimeout: 10s honorLabels: true # 标签冲突时保留应用自己的

**关键排错清单** ：

| 排查项               | 检查方式                                       |
|-------------------|--------------------------------------------|
| Label selector 匹配 | `release` label 是否匹配 Prometheus selector？  |
| Service label 匹配  | `matchLabels` 是否和 Service label 一致？        |
| 端口名对应             | `endpoints.port` 是否和 Service port name 一致？ |
| /metrics 可达       | Pod 内 `curl localhost:<port>/metrics` 能通吗？ |
| NetworkPolicy     | 是否阻止了 Prometheus → Pod 的流量？                |

### 3.2 Relabeling：采集前标签加工

Relabeling 是 ServiceMonitor 最强大的功能，允许在采集前后对标签做增删改。

| 阶段                         | 时机      | 作用                 |
|----------------------------|---------|--------------------|
| **relabel_configs**        | 采集前     | 控制采不采集、改 target 标签 |
| **metric_relabel_configs** | 采集后、存储前 | 过滤或修改指标标签          |

常用 Action：`replace`（默认，替换标签）、`keep`/`drop`（保留/丢弃匹配项）、`labeldrop`（删除某标签）。

## 四、PromQL 四维度查询

PromQL 是面向时间序列的函数式查询语言，几个核心函数：

rate(http_requests_total[5m]) # Counter 增长率（每秒） increase(http_requests_total[1h]) # 一小时总增长量 histogram_quantile(0.99, rate(..._bucket[5m])) # P99 分位数 sum(rate(http_requests_total[5m])) by (method) # 按方法分组聚合 topk(10, ...) # Top N

> **💡** **常见错误** ：对 Counter 直接 `sum()`——Counter 是累积值，直接加没意义。**永远先`rate()` 再 `sum()`。**

### 4.1 集群维度

# 集群 CPU 使用率 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) # 节点内存使用率 Top 5 topk(5, (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100) # API Server 错误率 sum(rate(apiserver_request_total{code=~"5.."}[5m])) / sum(rate(apiserver_request_total[5m])) * 100

### 4.2 Pod 维度

# CPU Top 10 Pod topk(10, sum(rate(container_cpu_usage_seconds_total{namespace!="kube-system"}[5m])) by (pod, namespace)) # Pod 重启次数 increase(kube_pod_container_status_restarts_total{namespace="production"}[1h]) # OOMKilled 事件 increase(container_oom_events_total[1h])

### 4.3 应用维度（RED 方法）

# R - Rate（QPS） sum(rate(http_requests_total{job="order-service"}[1m])) # E - Errors（5xx 错误率） sum(rate(http_requests_total{job="order-service",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="order-service"}[5m])) * 100 # D - Duration（P99 延迟） histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="order-service"}[5m])) by (le))

### 4.4 Recording Rule

频繁使用的复杂查询可以预计算：

apiVersion: monitoring.coreos.com/v1 kind: PrometheusRule metadata: name: recording-rules labels: release: kube-prometheus-stack spec: groups: \- name: precomputed interval: 1m rules: \- record: service:qps expr: sum by (job) (rate(http_requests_total[1m])) \- record: service:p99_latency expr: histogram_quantile(0.99, sum by (le, job) (rate(http_request_duration_seconds_bucket[5m])))

## 五、告警规则：从设计到上线

告警流程：**Prometheus 评估规则 → 条件满足 pending → 持续满足 firing → Alertmanager 分组/抑制/路由 → 通知渠道** 。

### 5.1 告警分级

| 级别     | 含义     | 响应时间     | 通知方式   | 典型场景               |
|--------|--------|----------|--------|--------------------|
| **P0** | 系统不可用  | 立即(24×7) | 电话+IM  | 全部节点 NotReady      |
| **P1** | 严重影响服务 | 15 分钟    | IM @全员 | 错误率 > 10%          |
| **P2** | 部分受影响  | 1 小时     | IM 群   | PVC > 85%、P99 > 2s |
| **P3** | 需关注    | 4 小时     | IM（不@） | 磁盘 > 70%           |

### 5.2 关键告警规则

**P0 节点宕机** ：

\- alert: NodeDown expr: up{job="node-exporter"} == 0 for: 3m labels: severity: critical level: P0 annotations: summary: "节点 {{ $labels.instance }} 宕机" description: "已离线超过 3 分钟，请立即检查！"

**P1 服务错误率过高** ：

\- alert: HighErrorRate expr: | sum(rate(http_requests_total{status=~"5.."}[5m])) by (job) / sum(rate(http_requests_total[5m])) by (job) > 0.10 for: 5m labels: severity: critical level: P0 annotations: summary: "服务 {{ $labels.job }} 5xx 错误率 > 10%"

**P1 P99 延迟过高** ：

\- alert: HighLatencyP99 expr: | histogram_quantile(0.99, sum by (le, job) (rate(http_request_duration_seconds_bucket[5m])) ) > 2 for: 5m labels: severity: high level: P1 annotations: summary: "服务 {{ $labels.job }} P99 延迟 > 2s"

**P2 磁盘即将写满** ：

\- alert: NodeDiskAlmostFull expr: | (1 - node_filesystem_avail_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes{fstype=~"ext4|xfs"}) * 100 > 90 for: 5m labels: severity: high level: P1

### 5.3 Alertmanager 分组与抑制

route: group_by: ['alertname', 'namespace'] group_wait: 30s # 第一次告警等 30s（收集同组） group_interval: 5m # 同组告警每 5 分钟发一次 repeat_interval: 4h # 同一告警 4 小时内不重复 inhibit_rules: # 节点宕机时，不告警上面的 Pod \- source_matchers: [alertname = "NodeDown"] target_matchers: [alertname =~ "PodCrashLoopBackOff|DeploymentReplicasMismatch"] equal: ['instance']

## 六、生产踩坑经验

### 坑 1：高基数标签 → Prometheus 内存爆炸

把 `user_id`、`trace_id`、URL 路径参数作为标签，会导致时间序列数量爆炸（10 万 user_id = 10 万条独立序列）。

**诊断** ：`topk(10, count by (__name__)({__name__=~".*"}))`

**修复** ：只保留低基数标签（method、endpoint 模板、status），**一个标签 unique 值超过 100 就要警惕** 。

### 坑 2：采集间隔太短 → 服务被打挂

`scrape_interval` 设为 1-5s，100 个 target 每秒产生大量请求。业务应用建议 **30-60s** 。

### 坑 3：Histogram 桶不合理 → P99 全错

默认桶可能不适合你的延迟范围。**先看 Grafana Heatmap 了解分布，再自定义 8-12 个桶** 。

### 坑 4：告警风暴 → 凌晨收到 200 条消息

一个节点挂了，50 个 Pod 各触发 3-4 条告警。**必须配置 Alertmanager 分组和抑制规则** 。

### 坑 5：滚动更新误报 → DeploymentReplicasMismatch

kube-state-metrics 有传播延迟。`for` 时间至少是正常运维操作的 **2-3 倍** （建议 10 分钟）。

### 坑 6：磁盘写满 → 数据丢失

容量估算：10 万序列 × 30s 间隔 × 15 天 ≈ **15GB** （含索引和 WAL）。配 `retentionSize` 自动清理。

## 七、可观测性全景：Prometheus 的位置

| 支柱              | 工具                   | 回答的问题       |
|-----------------|----------------------|-------------|
| **Metrics（指标）** | Prometheus + Grafana | 发生了什么？      |
| **Logs（日志）**    | Loki / EFK           | 细节是什么？      |
| **Traces（链路）**  | Jaeger / Tempo       | 在哪断裂的？      |
| **Events（事件）**  | K8s Events           | K8s 为什么这么做？ |

Prometheus 解决了 Metrics 这一环。

## 总结

| 知识点            | 关键内容                                                |
|----------------|-----------------------------------------------------|
| 应用指标暴露         | Java 用 Micrometer、Python 用 prometheus-client        |
| ServiceMonitor | 声明式采集配置，注意 label 匹配和端口对应                            |
| PromQL 核心      | `rate()` → Counter 增长率；`histogram_quantile()` → 分位数 |
| 告警分级           | P0(立即) / P1(15min) / P2(1h) / P3(4h)                |
| Alertmanager   | 分组 + 抑制 + 路由，避免告警风暴                                 |
| ⚠️ 最多人踩的坑      | 高基数标签、采集过频、Histogram 桶配置                            |

> **下一篇预告** ：第 25 篇：K8s 日志管理——EFK vs Loki，该选谁？

> 📢「从零开始学 Kubernetes」系列持续更新中，关注不迷路！ 

