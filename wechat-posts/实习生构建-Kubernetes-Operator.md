# 实习生构建 Kubernetes Operator

**作者**: 云原生AI视界
**发布时间**: 2026-07-15 07:14
**原文链接**: https://mp.weixin.qq.com/s/5OnflNLvRC7Zi8uPn_Ob3w

---

# 实习生构建 Kubernetes Operator

![cover](https://r2.jeanjan.kdns.fr/pictures/img-51eaac7901.jpeg)

当我加入 Red Hat 时，团队正在开发 Kagenti Operator——一个自动化 AI Agent 部署、安全和身份管理的开源 Kubernetes Operator。六个控制器、两个 webhook、数千行 Go 代码。这对三个第一天报到的实习生来说信息量太大了。

所以团队设计了一个缩小版让我们从零开始构建。同样的模式、同样的工具、同样的工作流，但只聚焦核心功能：一个 CRD、一个控制器、一个 webhook。我们叫它 Agenix。用两周时间自己搭建一个迷你版 Kagenti，学会基础，然后为真正的项目做贡献。我们之前没人写过 Go，也没用过 Kubernetes。

## 从基础开始

在写任何代码之前，我们做了一套 25 道题的 Kubernetes 基础测验。目的不是考我们，而是找出知识盲区，让团队有针对性地教学。之后我们拿到了一份设计文档和一组 Jira ticket，每个 ticket 都附带学习练习。以团队方式 onboard 比独自看文档有效得多——你可以互相提问、一起卡在同一个问题上，不会觉得孤立。

我的部分是构建 CRD、控制器和证书配置，通过五个 PR 合入。队友们负责 CA、mutating webhook、验证逻辑和 finalizer。我们互相 review 每一个 PR。

## 故意搞坏东西

每个 Jira ticket 都附带学习练习，要求我们故意搞坏东西并记录为什么会坏。这是项目中节奏最慢但最让我受益的部分——猜测会发生什么，通常猜错，然后搞明白为什么。

**删除 CRD 时存在自定义资源。** 我的示例 CR 消失了。重新安装 CRD 后定义回来了，但实例数为零。删除 CRD 时 Kubernetes 会连带删除该类型的所有自定义资源。

**让叶子证书自签名而不是由 CA 签名。** 链验证失败。我最初以为任何东西都不能自签名，但 CA 是例外——它是信任根，上面没有更高的签发者。没有链验证，任何 Agent 都可以自己签证书冒充任意身份。

**手动移除 finalizer。** Kubernetes 立即处理了删除，但清理逻辑从未执行。Secret 还在，Deployment 上的标签还在，什么都没被清理。没有 finalizer，Kubernetes 假设清理已经完成。

**移除 Secrets RBAC 标记后重新部署。** 本地没有报错，因为 `make run` 用的是我的 kubeconfig，拥有完整的 cluster-admin 权限。但作为 Pod 部署时，会收到 403 Forbidden。Kubernetes 要求你显式列出权限，Operator 只能触碰被授权访问的资源。

## 在彼此代码中找 Bug

我 review 了队友的八个 PR，发现了真正的 bug。第一次 review 时，我发现了一个空的 SPIFFE ID 被 Go 的 URL parser 静默接受。另一个 PR 中发现了一个路径注入风险——namespace 中的 `/` 可能破坏身份标识。

这些 review 让我理解了整个 Operator，而不仅仅是我负责的部分。

## 审视 AI

我在完成任务后用 AI 来测试自己是否真正理解了内容。我也用另一个会话作为独立代码审查者，在提交 PR 之前检查。它确实抓住了一个重复状态写入和缺失的错误处理。

但我们被提醒不要盲目接受 AI 的输出。有一次 Claude 告诉我 cert-manager 在 TTL 的 80% 时续签。我问"你确定吗？"它无法佐证。实际惯例是三分之二。很小的事情，但教会了我始终验证。

## 部署到 OpenShift

最后一步是把 Operator 从本地 Kind 集群迁移到 AWS 上的 Red Hat OpenShift。容器镜像架构不对、基础镜像不满足 OpenShift 安全要求、镜像需要放在公共 registry 上让集群能拉取。我逐一解决了这些问题，并写了一份部署指南让团队避免踩同样的坑。

## 真正学到的东西

通过构建真实的 Operator 来学习，远比看课程有效。使用团队实际需要的工具和模式，让 onboard 感觉有用而不是纸上谈兵。

在大学里，你提交作业拿到分数。在这里，我的代码进入了真实的仓库，会被拒绝如果不达标，而且必须在真实的集群上运行。两周结束时我们做了演示，工程师们说这是他们见过的最好的实习生展示之一。

源码在 GitHub 上：https://github.com/gracesmith6504/Agenix[1]

