# 我用 50 行 YAML 替换了 Jenkins

**作者**: 云原生AI视界
**发布时间**: 2026-08-05 06:54
**原文链接**: https://mp.weixin.qq.com/s/AdqIU0W7PO8W_SVn7DoKcQ

---

# 我用 50 行 YAML 替换了 Jenkins

![cover](images/img-eb5197f101.jpeg)

> Tekton Pipelines 把我的 CI/CD 变成了 Kubernetes 原生资源。没有 VM，没有插件，没有 Jenkins 维护周末。

上个月我杀掉了我们的 Jenkins 服务器。不是比喻，是 `kubectl delete`。我没有回头。

替代品是 **Tekton Pipelines** \-- 一个开源的 Kubernetes 原生 CI/CD 框架，整个构建流水线定义为 Kubernetes CRD。Task 是 Pod。Pipeline 是 YAML。Trigger 是自动创建 PipelineRun 的 webhook。

没有 Java，没有插件，没有 "manage Jenkins" 页面。只有 Kubernetes 资源。

## 问题：CI/CD 不应该需要自己的基础设施

如果你管理过 Jenkins，你知道那种痛：

  * 每次更新后的插件兼容性地狱
  * 6 个月后没人理解的 Groovy 脚本
  * 专门跑构建的 VM（或三台）
  * "在我的 Jenkins 上能跑" 作为调试语句
  * 让安全团队夜不能寐的凭据管理

GitHub Actions 有帮助。但它仍然是运行在集群_之外_的专有平台。构建发生在别处，密钥存在别处，你为自己已有的计算能力按分钟付费。

**如果你的 CI/CD 流水线只是另一个 Kubernetes 工作负载呢？** 那就是 Tekton。

## Tekton 实际上是什么（60 秒版）

Tekton 作为一组 CRD 安装在你的 Kubernetes 集群中。四个核心概念：

  * **Task** \-- 一个包含多个 Step 的可复用构建单元，每个 Step 是一个容器
  * **Pipeline** \-- 有序的 Task 集合，定义执行顺序和依赖关系
  * **TaskRun** \-- Task 的一次执行实例
  * **PipelineRun** \-- Pipeline 的一次执行实例

没有服务器要维护，没有 UI 要配置。一切都是 YAML，版本化在 Git 中，用 `kubectl` 应用。

## 完整 CI/CD 流水线

整个流水线看起来是这样的：
```

apiVersion: tekton.dev/v1  
kind: Pipeline  
metadata:  
  name: build-test-deploy  
spec:  
  tasks:  
    - name: clone          # 克隆 Git 仓库  
      taskRef: { name: git-clone }  
    - name: lint           # Python 代码检查  
      taskRef: { name: lint-code }  
      runAfter: [clone]  
    - name: build          # 用 Kaniko 构建容器（不需要 Docker daemon）  
      taskRef: { name: build-image }  
      runAfter: [lint]  
    - name: deploy         # kubectl set image + rollout  
      taskRef: { name: deploy-app }  
      runAfter: [build]  
    - name: test           # 对线上端点做冒烟测试  
      taskRef: { name: run-tests }  
      runAfter: [deploy]  

```

五个 Task，五个 Pod。每个运行、完成，通过共享 workspace 将数据传递给下一个。整个过程约 90 秒。

## Tekton vs Jenkins：实际对比

| 维度   | Jenkins              | Tekton             |
|------|----------------------|--------------------|
| 运行方式 | 专用服务器/VM             | Kubernetes Pod     |
| 配置语言 | Groovy (Jenkinsfile) | YAML (CRD)         |
| 插件管理 | 手动安装、兼容性问题           | 容器镜像即插件            |
| 扩展方式 | 增加 Jenkins agent     | Kubernetes 自动伸缩    |
| 密钥管理 | Jenkins credentials  | Kubernetes Secrets |
| 版本控制 | Jenkinsfile in Git   | 全部 CRD in Git      |
| UI   | 必须使用                 | 可选 Dashboard       |

## Tekton 的核心优势

**一切都是 Kubernetes 资源。** Task 是 Pod，Pipeline 是 CRD，执行历史是 PipelineRun。你可以用 `kubectl get pipelineruns` 查看 CI/CD 历史，就像查看 Deployment 一样自然。

**容器即插件。** 需要新工具？用包含它的容器镜像。不需要安装插件、重启服务、担心兼容性。每个 Step 是一个独立容器，完全隔离。

**Kaniko 构建镜像。** Tekton 不需要 Docker daemon。Kaniko 在容器内直接从 Dockerfile 构建镜像并推送到仓库，无需特权模式，更安全。

**GitOps 原生。** 所有流水线定义都在 Git 中。变更通过 PR 审查、版本追踪。回滚就是 `git revert` \+ `kubectl apply`。

## Triggers：自动触发

Tekton Triggers 让流水线自动响应 Git 事件。推送到 main 分支自动触发部署，创建 PR 自动触发测试。Webhook 接收 Git 事件，创建对应的 PipelineRun。

## 总结

Tekton 不是 Jenkins 的直接替代品--它是一种思维方式的转变。CI/CD 不再是一个需要维护的外部系统，而是 Kubernetes 集群的 native 居民。

如果你已经在运行 Kubernetes，Tekton 是最自然的 CI/CD 选择。没有额外的服务器、没有插件地狱、没有 Groovy。只有 YAML、Pod 和 Git。

完整演示代码：GitHub: tekton-in-action[1]

