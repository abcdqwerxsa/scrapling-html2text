# K8s Operator入门：CRD自定义控制器

**作者**: 玥哲
**发布时间**: 2026-08-10 09:01
**原文链接**: https://mp.weixin.qq.com/s/x8s7Ge0XljFff42wX9tO0A

---

## 开篇场景

周五下午，你接到一个任务：在 K8s 上部署 MySQL 主从集群，要求主从复制、自动故障切换、定时备份。你翻了 StatefulSet 文档，发现它能按顺序创建 Pod、分配稳定存储，但**做不到** 自动配置主从关系、故障选举、定时备份。

于是你写了 15 个 YAML + 3 个脚本，终于跑起来了。然后主节点挂了，凌晨 3 点被电话叫醒……

**这就是 Operator 要解决的问题。** Operator 把运维知识编码成软件，让 K8s 自动处理复杂操作——数据复制、备份、故障切换，任何脚本能做的事它都能做。

## 一、什么是 Operator？

> **Operator = CRD（定义"你要什么"）+ Controller（自动实现"怎么做"）**

| 传统运维        | K8s Operator         |
|-------------|----------------------|
| 运维人员看监控告警   | Controller 监听 CRD 事件 |
| 运维人员执行恢复脚本  | Controller 自动执行调谐逻辑  |
| 运维人员更新配置文档  | 用户更新 CR 的 YAML       |
| 运维人员值班 24×7 | Controller 7×24 自动运行 |

**Operator 本质上是一个"编码的运维工程师"。**

### 工作流程

1\. 用户创建 `MySQLCluster` 自定义资源（CR），声明"我要 1 主 2 从"2\. Controller 监听到新 CR 被创建3\. Reconcile 逻辑触发，创建 StatefulSet、Service、ConfigMap 等资源4\. Controller 持续观察集群，发现主节点故障时自动切换

![](https://r2.jeanjan.kdns.fr/pictures/img-f7d242f901.png)

### 为什么不用 Helm / Kustomize？

| 工具            | 适合场景            | 局限            |
|---------------|-----------------|---------------|
| **Helm**      |  一次性部署静态配置      | 部署完就走了，不管后续运维 |
| **Kustomize** |  多环境配置覆盖        | 同上，只是模板工具     |
| **Operator**  |  持续管理有状态应用全生命周期 | 开发成本较高        |

> **Helm 是"快递员"——送到就走；Operator 是"管家"——全程负责。**

## 二、核心概念详解

### 2.1 CRD（Custom Resource Definition）

向 K8s 注册一种新资源类型。注册后 `kubectl` 就能认识它：
```

kubectl get mysqlclusters
kubectl describe mysqlcluster my-db
kubectl apply -f my-database.yaml
```

CRD 本身只是"schema 定义"，类似数据库的表结构，声明字段和类型。

### 2.2 Custom Resource（CR）

CR 是 CRD 的一个实例，类似表中的一行记录：
```

apiVersion: database.example.com/v1alpha1
kind: MySQLCluster
metadata:
  name: my-app-db
spec:
  replicas: 3
  version: "8.0"
  backup:
    schedule: "0 2 * * *"
    storageLocation: "s3://my-bucket/backups"
```

用户通过创建和修改 CR 表达"我要什么"，Controller 负责"怎么做"。

### 2.3 Controller（控制器）与 Reconciliation Loop

Controller 是常驻进程，核心是 **Reconciliation Loop** （调谐循环）：
```

┌──────────────────────────────────────────────┐
│           Reconciliation Loop                │
│                                              │
│   ┌─────────────┐                            │
│   │  观察状态    │ ◄─── 从 K8s API 读取      │
│   └──────┬──────┘                            │
│          ▼                                   │
│   ┌─────────────┐                            │
│   │  对比差异    │ ◄─── 期望 vs 实际         │
│   └──────┬──────┘                            │
│          ▼                                   │
│   ┌─────────────┐                            │
│   │  执行调谐    │ ───► 写入 K8s API          │
│   └─────────────┘     （创建/更新/删除资源）   │
│                                              │
└──────────────────────────────────────────────┘
```

![](https://r2.jeanjan.kdns.fr/pictures/img-f7d242f902.png)

**关键特性：幂等性** 。无论 Reconcile 被触发多少次，结果一样。因为每次都是"观察 → 对比 → 修复差异"，而非按顺序执行步骤。

### 2.4 Informer 和 Cache 机制

Controller 怎么知道资源变化了？实际使用的是 **Informer** ：订阅事件流 + 本地缓存。
```

K8s API Server ──(Watch 事件流)──► Informer
                                     │
                          ┌──────────┴──────────┐
                          │                      │
                     本地 Cache              事件队列
                   （快速读取）            （触发 Reconcile）
```

好消息：Kubebuilder 和 Operator SDK 已帮你封装好这些底层机制，你只需实现 Reconcile 方法。

### 2.5 声明式 vs 命令式
```

# 声明式（Operator 风格）：告诉系统"我要什么状态"
apiVersion: database.example.com/v1alpha1
kind: MySQLCluster
spec:
  replicas: 3    # 我要 3 个实例
  mode: primary-secondary  # 主从模式
```

Controller 读到"我要 3 个"，自己决定怎么创建。已有 3 个就不管，有 5 个就删 2 个。

## 三、第一个 CRD：定义自定义资源

### 场景：WebApp Operator

定义一个 `WebApp` CRD，用户只需声明镜像、副本数和域名，Operator 自动创建 Deployment、Service 和 Ingress。

### 定义 CRD
```

# webapp-crd.yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: webapps.webapp.example.com
spec:
  group: webapp.example.com
  names:
    kind: WebApp
    plural: webapps
    shortNames: ["wa"]
  scope: Namespaced
  versions:
  - name: v1alpha1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: ["image"]
            properties:
              image: { type: string }
              replicas: { type: integer, default: 1 }
              port: { type: integer, default: 80 }
              host: { type: string }
          status:
            type: object
            properties:
              readyReplicas: { type: integer }
              podNames:
                type: array
                items: { type: string }
              url: { type: string }
```

> 💡 相比完整版，这里精简了 `resources` 嵌套定义，只保留核心字段 image/replicas/port/host。生产环境建议加上资源限制验证。 

### 创建 CRD 并验证
```

kubectl apply -f webapp-crd.yaml
kubectl get crd | grep webapp
```

### 创建 CR 实例
```

apiVersion: webapp.example.com/v1alpha1
kind: WebApp
metadata:
  name: my-site
  namespace: production
spec:
  image: nginx:1.25
  replicas: 3
  port: 80
  host: my-site.example.com

kubectl apply -f my-webapp.yaml
kubectl get wa -n production
```

输出：
```

NAME     IMAGE         REPLICAS   READY   AGE
my-site  nginx:1.25    3          0       5s
```

> `READY` 列显示 0，因为还没有 Controller 来处理它。接下来写 Controller。 

## 四、编写 Controller：调谐循环实战

### 使用 Kubebuilder

Kubebuilder 是 K8s 官方推荐的 Operator 开发框架，提供项目脚手架、代码生成、测试框架、Makefile。
```

# 安装（前置：Go 1.21+）
curl -L -o kubebuilder "https://go.kubebuilder.io/dl/latest/$(go env GOOS)/$(go env GOARCH)"
chmod +x kubebuilder && mv kubebuilder /usr/local/bin/

# 创建项目
mkdir webapp-operator && cd webapp-operator
go mod init github.com/example/webapp-operator
kubebuilder init --domain example.com --repo github.com/example/webapp-operator
kubebuilder create api \
  --group webapp --version v1alpha1 --kind WebApp \
  --resource --controller
```

![](https://r2.jeanjan.kdns.fr/pictures/img-f7d242f903.png)

### 定义 Go 类型

编辑 `api/v1alpha1/webapp_types.go`：
```

package v1alpha1

import metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

type WebAppSpec struct {
    Image    string `json:"image"`
    Replicas int32  `json:"replicas,omitempty"`
    Port     int32  `json:"port,omitempty"`
    Host     string `json:"host,omitempty"`
}

type WebAppStatus struct {
    ReadyReplicas     int32        `json:"readyReplicas,omitempty"`
    PodNames          []string     `json:"podNames,omitempty"`
    URL               string       `json:"url,omitempty"`
    LastReconcileTime *metav1.Time `json:"lastReconcileTime,omitempty"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
type WebApp struct {
    metav1.TypeMeta   `json:",inline"`
    metav1.ObjectMeta `json:"metadata,omitempty"`
    Spec   WebAppSpec   `json:"spec,omitempty"`
    Status WebAppStatus `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
type WebAppList struct {
    metav1.TypeMeta `json:",inline"`
    metav1.ListMeta `json:"metadata,omitempty"`
    Items           []WebApp `json:"items"`
}
```

> 💡 `+kubebuilder:` 注释是标记（marker），`make manifests` 会读取它们自动生成 CRD YAML 和 RBAC 规则。 

### 实现 Reconcile 方法

Reconcile 是 Controller 的核心。编辑 `internal/controller/webapp_controller.go`，核心逻辑分 6 步：
```

func (r *WebAppReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    logger := log.FromContext(ctx)

    // ===== 步骤 1：获取 CR 实例 =====
    var webapp webappv1alpha1.WebApp
    if err := r.Get(ctx, req.NamespacedName, &webapp); err != nil {
        if errors.IsNotFound(err) {
            return ctrl.Result{}, nil // 已删除
        }
        return ctrl.Result{}, err
    }

    // ===== 步骤 2：确保 Deployment 存在 =====
    deployment := r.buildDeployment(&webapp)
    _ = controllerutil.SetControllerReference(&webapp, deployment, r.Scheme)

    var existingDeploy appsv1.Deployment
    err := r.Get(ctx, types.NamespacedName{
        Name: deployment.Name, Namespace: webapp.Namespace,
    }, &existingDeploy)

    if errors.IsNotFound(err) {
        logger.Info("创建 Deployment")
        _ = r.Create(ctx, deployment)
    } else if err == nil {
        if *existingDeploy.Spec.Replicas != webapp.Spec.Replicas ||
            existingDeploy.Spec.Template.Spec.Containers[0].Image != webapp.Spec.Image {
            existingDeploy.Spec = deployment.Spec
            _ = r.Update(ctx, &existingDeploy)
        }
    }

    // ===== 步骤 3：确保 Service 存在（逻辑同上）=====
    svc := r.buildService(&webapp)
    // ... Get -> NotFound 则 Create

    // ===== 步骤 4：如果配置了域名，创建 Ingress =====
    if webapp.Spec.Host != "" {
        // Get -> NotFound 则 Create
    }

    // ===== 步骤 5：更新 Status =====
    webapp.Status.ReadyReplicas = existingDeploy.Status.ReadyReplicas
    webapp.Status.LastReconcileTime = &metav1.Time{Time: time.Now()}
    webapp.Status.URL = fmt.Sprintf("http://%s", webapp.Spec.Host)
    _ = r.Status().Update(ctx, &webapp)

    // ===== 步骤 6：副本数未达标则重新排队 =====
    if webapp.Status.ReadyReplicas != webapp.Spec.Replicas {
        return ctrl.Result{RequeueAfter: 30 * time.Second}, nil
    }
    return ctrl.Result{}, nil
}
```

### 辅助方法与注册
```

func (r *WebAppReconciler) buildDeployment(w *webappv1alpha1.WebApp) *appsv1.Deployment {
    replicas := w.Spec.Replicas
    return &appsv1.Deployment{
        ObjectMeta: metav1.ObjectMeta{Name: w.Name, Namespace: w.Namespace},
        Spec: appsv1.DeploymentSpec{
            Replicas: &replicas,
            Selector: &metav1.LabelSelector{
                MatchLabels: map[string]string{"app": w.Name},
            },
            Template: corev1.PodTemplateSpec{
                ObjectMeta: metav1.ObjectMeta{Labels: map[string]string{"app": w.Name}},
                Spec: corev1.PodSpec{Containers: []corev1.Container{{
                    Name: "app", Image: w.Spec.Image,
                    Ports: []corev1.ContainerPort{{ContainerPort: w.Spec.Port}},
                }}},
            },
        },
    }
}

func (r *WebAppReconciler) buildService(w *webappv1alpha1.WebApp) *corev1.Service {
    return &corev1.Service{
        ObjectMeta: metav1.ObjectMeta{Name: w.Name, Namespace: w.Namespace},
        Spec: corev1.ServiceSpec{
            Selector: map[string]string{"app": w.Name},
            Ports: []corev1.ServicePort{{
                Port: w.Spec.Port,
                TargetPort: intstr.FromInt(int(w.Spec.Port)),
            }},
        },
    }
}

// SetupWithManager 注册 Controller 到 Manager
func (r *WebAppReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&webappv1alpha1.WebApp{}).
        Owns(&appsv1.Deployment{}).
        Owns(&corev1.Service{}).
        Complete(r)
}
```

> 💡 精简说明：删除了 `buildIngress` 和 `buildResourceRequirements`；`SetControllerReference` 设置 OwnerReference，确保 CR 删除时关联资源自动清理。 

## 五、高级特性概览

以下是 Operator 开发中常用的高级特性，每个都值得单独深入学习：

| 特性                    | 作用          | 说明                                               |
|-----------------------|-------------|--------------------------------------------------|
| **Status 子资源**        |  记录资源当前实际状态 | 用户通过 kubectl describe 查看进度，与 spec 期望状态分离         |
| **OwnerReference**    |  建立资源间的父子关系 | CR 删除时，K8s 自动级联删除关联的 Deployment/Service/Pod      |
| **Finalizer**         |  阻止删除直到清理完成 | Controller 收到删除事件后先执行清理（备份、释放外部资源），再移除 Finalizer |
| **Admission Webhook** |  变更前/后拦截校验  | 验证 CR 字段合法性、设置默认值、拒绝非法操作                         |

## 六、真实 Operator 案例参考

### MySQL Operator（Oracle 官方）

Oracle 官方维护的 MySQL Operator，支持 InnoDB Cluster 部署。用户只需声明一个 `InnoDBCluster` CR，Operator 自动处理 Group Replication 配置、主节点选举、备份恢复和滚动升级。适合生产环境使用。

### Prometheus Operator（CoreOS/Red Hat）

监控领域的标杆 Operator。通过 `ServiceMonitor` 和 `Prometheus` CR 自动发现服务、生成抓取配置、管理 Prometheus 实例生命周期。K8s 监控体系的事实标准。

## 七、框架选型

| 框架                    | 语言               | 特点            | 适合场景                             |
|-----------------------|------------------|---------------|----------------------------------|
| **Kubebuilder**       |  Go              | K8s 官方推荐，生态最好 | Go 技术栈、需要最大灵活性                   |
| **Operator SDK**      |  Go/Ansible/Helm | 支持多语言，低门槛     | 已有 Ansible Playbook 或 Helm Chart |
| **Metacontroller**    |  YAML            | 无需写代码         | 简单场景、快速原型                        |
| **Java Operator SDK** |  Java            | JVM 生态        | Java 技术栈团队                       |

> 大多数生产级 Operator 选择 **Kubebuilder** ，本文示例也基于它。 

## 八、生产注意事项

• **RBAC 最小权限** ：只授予 Controller 必要的 API 权限，避免过大的 ClusterRole• **优雅关闭** ：处理 SIGTERM 信号，确保正在进行的 Reconcile 能完成• **错误处理** ：区分可重试错误和永久错误，避免无限循环消耗 API Server• **资源隔离** ：Operator Pod 建议设置资源限制，避免与业务 Pod 竞争• **多实例部署** ：通过 Leader Election 确保同一时间只有一个 Controller 实例在工作• **版本演进** ：CRD 使用 v1alpha1 → v1beta1 → v1 版本号，用 Conversion Webhook 处理版本间转换• **可观测性** ：Controller 输出结构化日志，暴露 Metrics 端点供 Prometheus 抓取• **测试覆盖** ：用 envtest 做单元测试，用 kind/minikube 做集成测试

## 总结

本文从"为什么需要 Operator"出发，覆盖了 Operator 的核心概念和实战开发：

1\. **Operator = CRD + Controller** ，本质是"编码的运维工程师"2\. **CRD** 定义新的资源类型，**CR** 是具体实例，**Controller** 通过 Reconciliation Loop 持续调谐3\. 使用 **Kubebuilder** 快速搭建项目，只需实现 Reconcile 方法4\. 高级特性（Status/OwnerReference/Finalizer/Webhook）让 Operator 更健壮5\. 框架选型以 Kubebuilder 为主流，生产环境还需关注 RBAC、Leader Election、可观测性  

📢 「从零开始学 Kubernetes」系列持续更新中，关注不迷路！

