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

### 爬取微信公众号文章

```python
from main import crawl_wechat_article

crawl_wechat_article(
    "https://mp.weixin.qq.com/s/xxxxxx",
    output_file="article.md"
)
```

### 爬取任意网页

```python
from main import crawl_webpage

crawl_webpage(
    "https://github.com/D4Vinci/Scrapling",
    output_file="github.md"
)
```

### 命令行使用

```bash
# 爬取微信公众号
uv run python -c "
from main import crawl_wechat_article
crawl_wechat_article('https://mp.weixin.qq.com/s/xxxxxx', 'article.md')
"

# 爬取普通网页
uv run python -c "
from main import crawl_webpage
crawl_webpage('https://example.com/blog', 'blog.md')
"
```

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
