# Scrapling + HTML2Text

使用 Scrapling + html2text 爬取网页内容并转换为干净的 Markdown 格式。特别适用于微信公众号等有反爬机制的网站。

## 核心优势

| 特性 | 说明 |
|------|------|
| 绕过反爬 | Scrapling 原生支持绕过 Cloudflare、微信等反爬机制 |
| 格式保留 | html2text 保留链接、图片、列表、强调等格式 |
| 无限制 | 无 API 调用限制，无需 API Key |
| 微信支持 | 可直接爬取微信公众号文章（Jina/web_fetch 无法做到） |

## 环境准备

### 1. 安装 uv（推荐）

uv 是一个极速的 Python 包管理器，比 pip 快 10-100 倍。

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 安装 Python 3.13+

本项目使用 Python 3.13，可以通过 uv 安装：

```bash
uv python install 3.13
```

### 3. 克隆项目

```bash
git clone https://github.com/abcdqwerxsa/scrapling-html2text.git
cd scrapling-html2text
```

### 4. 安装依赖

```bash
# 安装 Python 依赖
uv sync

# 安装 Playwright 浏览器（必需）
uv run playwright install chromium
```

## 快速开始

### 命令行使用（推荐）

```bash
# 爬取微信公众号文章（自动识别，保存到 wechat-posts/，文件名取文章标题）
uv run python main.py 'https://mp.weixin.qq.com/s/xxxxxx'

# 指定输出目录
uv run python main.py 'https://mp.weixin.qq.com/s/xxxxxx' -o my-articles

# 爬取普通网页
uv run python main.py 'https://github.com/D4Vinci/Scrapling' -o github
```

### 作为库调用

两个函数都返回 Markdown 文本，不直接写文件；传入 `images_dir` 可把微信图片下载到本地（绕过防盗链）：

```python
from pathlib import Path
from main import crawl_wechat_article, crawl_webpage

# 微信公众号：标题/作者/发布时间 + 正文，图片下载到 images/
markdown = crawl_wechat_article(
    "https://mp.weixin.qq.com/s/xxxxxx",
    images_dir=Path("wechat-posts/images"),
)
Path("article.md").write_text(markdown, encoding="utf-8")

# 任意网页：自动探测标题与正文
markdown = crawl_webpage("https://github.com/D4Vinci/Scrapling")
```

### 内置修复（微信文章常见坑）

| 问题 | 处理 |
|------|------|
| 图片懒加载 | `data-src` → `src` |
| 图片防盗链 | 上传 R2 图床并引用公网 URL；未配置时回退下载本地 `images/` |
| 代码块挤成一行 | `</code><code>` 之间补换行，转 ```` ``` ````围栏 |
| 装饰性分隔点 | 清理被误转的空列表项 |
| 发布时间 JS 渲染 | 从页面内嵌 `var ct` 时间戳恢复 |

### R2 图床配置（可选，不配则图片存本地）

在项目根目录创建 `r2-config.json`（已 gitignore，勿提交）：

```json
{
  "endpoint": "https://<account>.r2.cloudflarestorage.com",
  "bucket": "<bucket>",
  "accessKeyID": "<ak>",
  "secretAccessKey": "<sk>",
  "keyPrefix": "pictures",
  "publicBase": "https://<绑定到桶的自定义域名>"
}
```

`publicBase` 必须是绑定到该桶根路径的公网域名（R2 自定义域名），最终图片 URL 为
`{publicBase}/{keyPrefix}/{文件名}`。删除或重命名此文件即回退本地存图。

## 支持的网站类型

| 网站 | 支持情况 | 说明 |
|------|---------|------|
| 微信公众号 | 完美支持 | 图片、格式全保留 |
| GitHub | 完美支持 | README、代码块完整 |
| 技术博客 | 完美支持 | Medium、Substack、WordPress 等 |
| 新闻网站 | 良好 | 自动提取正文 |
| 其他网站 | 良好 | 自动检测正文选择器 |

## 方案对比

| 方案 | 微信公众号 | 反爬网站 | 每日限制 | 格式质量 |
|------|-----------|---------|---------|---------|
| **Scrapling + html2text** | 支持 | 支持 | 无限制 | 优秀 |
| Jina Reader | 不支持 | 部分支持 | 200次/天 | 优秀 |
| web_fetch | 不支持 | 不支持 | 无限制 | 差（全页噪音） |

## 项目结构

```
scrapling-html2text/
├── main.py                    # 主程序
├── pyproject.toml             # 项目配置
├── README.md                  # 本文件
└── .claude/skills/
    └── webpage-to-markdown/   # Claude Code Skill
        ├── SKILL               # 技能说明
        ├── templates/          # 代码模板
        ├── examples/           # 使用示例
        └── config/             # 配置预设
```

## 依赖说明

| 依赖 | 用途 |
|------|------|
| scrapling | 网页爬取，绕过反爬 |
| html2text | HTML 转 Markdown |
| playwright | 浏览器自动化（Scrapling 依赖） |
| browserforge | 浏览器指纹生成 |
| curl-cffi | HTTP 请求库 |

## 常见问题

### Q: 为什么要用 Playwright？

Scrapling 使用 Playwright 来模拟真实浏览器行为，绑过反爬检测。首次使用需要安装浏览器：

```bash
uv run playwright install chromium
```

### Q: 图片为什么显示不出来？

微信公众号使用 `data-src` 延迟加载图片，本项目已自动处理转换。

### Q: 代码块格式不对？

本项目会自动将缩进代码块转换为 ``` 格式，确保 Markdown 渲染正确。

### Q: 遇到更强的反爬怎么办？

可以使用 Scrapling 的 `StealthyFetcher`：

```python
from scrapling import StealthyFetcher

fetcher = StealthyFetcher()
page = fetcher.get(url)
```

## 相关链接

- [Scrapling GitHub](https://github.com/D4Vinci/Scrapling)
- [html2text PyPI](https://pypi.org/project/html2text/)
- [Playwright 文档](https://playwright.dev/python/)
- [uv 官网](https://docs.astral.sh/uv/)

## License

MIT
