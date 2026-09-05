---
description: 爬取微信文章转Markdown（多图自动进R2图床，支持批量）
argument-hint: "<微信文章URL，可多个>"
---
执行微信文章爬取流程，在项目 /home/nilpo/scrapling-html2text 中运行：

```bash
cd /home/nilpo/scrapling-html2text && uv run python main.py $@
```

脚本自动完成：爬取正文 → Markdown 存入本次运行的日期文件夹（wechat-posts/YYYY-MM-DD，同日重跑自动加时间戳后缀）→ 图片上传 R2 图床并引用公网 URL（代码块/发布时间/装饰点等微信格式问题自动修复）。支持一次传多个 URL。

执行后向用户报告：成功保存的文件路径列表、失败项及原因。
