---
description: 爬取微信文章转Markdown并同步到WeKnora知识库（图片自动进R2图床+图像理解）
argument-hint: "<微信文章URL，可多个>"
---
执行微信文章同步流程，在项目 /home/nilpo/scrapling-html2text 中运行：

```bash
cd /home/nilpo/scrapling-html2text && uv run python sync_weknora.py $@
```

脚本自动完成：爬取正文 → Markdown 存入 wechat-posts/（标题命名）→ 图片上传 R2 图床引用公网 URL → 删除 WeKnora 同名旧文档（幂等）→ 上传 demo-wechat 知识库（图像处理已开启）→ 轮询解析状态。

执行后向用户报告：成功/失败篇数、解析失败的文档及原因。前置依赖：本机 Docker 的 WeKnora 栈在运行；若脚本报知识库不存在或认证失败，检查 WeKnora 容器状态后重试。
