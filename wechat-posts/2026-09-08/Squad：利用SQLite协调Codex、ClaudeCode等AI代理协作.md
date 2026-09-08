# Squad：利用SQLite协调Codex、ClaudeCode等AI代理协作

**作者**: AI工程化
**发布时间**: 2026-08-31 17:41
**原文链接**: https://mp.weixin.qq.com/s/tTtNNYy3oDDJS5CJPjb7pA

---

当前Codex、ClaudeCode众多Agent工具，对于开发者来讲是再做一个类似的产品，还是把它们用起来，强强联合，这代表了两个产品方向。

对于tokenbank（一款可以跨用户共享智能体和模型的开源AI中枢）产品来讲就是后者，毕竟，重做一个不如将它们的优点整合起来更有意义。

![](https://r2.jeanjan.kdns.fr/pictures/img-961d583a01.png)

那么，接下来一个问题就摆在面前，如何让这些智能体有机的协作呢？

今天，介绍一个项目，它让多个 AI 代理在终端里协作，靠 shell 命令和 SQLite 通信。没有守护进程，没有后台服务，每个命令跑完就结束了。

![squad multi-agent terminal collaboration through SQLite](https://r2.jeanjan.kdns.fr/pictures/img-961d583a02.png)

支持 Claude Code、Gemini CLI、Codex CLI、OpenCode 四个平台。

做法很简单。每个代理干完活，把结果写进同一个 SQLite 数据库。下一个代理读库，接着干。没有常驻编排服务，协调就是数据库读写。

三个内置角色：

  * **manager** ：拆目标、分任务、协调审查
  * **worker** ：执行任务、汇报结果
  * **inspector** ：审查代码，输出 PASS/FAIL

角色文件是 `.md`，放在 `.squad/roles/` 下。想加就加，比如丢个 `dba.md`，然后 `squad join db-expert --role dba`。

任务系统有完整生命周期。`task create` 创建，`task ack` 认领，`task complete` 提交结果带 summary，`task requeue` 可以塞回队列甚至换人接手。README 建议优先用 task 命令处理有状态任务，`send`/`receive` 留给自由协调用。

agent 的工作循环：join 进来，`squad receive --wait` 阻塞等消息，收到任务 ack 认领，干完 complete 提交，继续 block 等下一个。不带 `--wait` 就是查一次立刻返回，脚本里用。

ID 冲突处理得干净。多个 agent 用同一个 ID join，自动变成 `worker-2`、`worker-3`。底层是 SQLite 的 `INSERT OR IGNORE`，同时 join 也不会出竞态。广播也支持：`squad send manager @all "API 合约改了"`，一条命令全收到。

安装：macOS `brew install mco-org/tap/squad`，Windows 去 GitHub Releases 拿预编译包，或者 `cargo install --git` 源码编。需要 Rust 1.77+。

Squad 刚发布，MIT 许可。手头有多个 CLI 代理想让他们配合干活，可以试试。先让两个代理通过 SQLite 说上话，比先设计一套漂亮架构靠谱。

仓库地址：

https://github.com/mco-org/squad

https://github.com/wink-run/tokenbank

关注公众号回复“进群”入群讨论

