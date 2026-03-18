---
name: webpage-to-markdown
description: 使用 scrapling + html2text 爬取网页内容（特别是微信公众号文章）并转换为 Markdown 格式
version: 1.1.0
source: workflow-extraction
triggers:
  - 爬取网页
  - 抓取微信公众号
  - 网页转 Markdown
  - HTML 转 Markdown
files:
  - templates/crawler.py           # 完整代码模板
  - examples/wechat-output.example # 输出示例
  - config/html2text-presets.py    # 配置预设
---

# 网页内容爬取转 Markdown

使用 Scrapling + html2text 组合爬取网页内容并转换为干净的 Markdown 格式。特别适用于微信公众号等有反爬机制的网站。

## 核心优势

| 特性 | 说明 |
|------|------|
| 绕过反爬 | Scrapling 原生支持绕过 Cloudflare、微信等反爬机制 |
| 格式保留 | html2text 保留链接、图片、列表、强调等格式 |
| 无限制 | 无 API 调用限制，无需 API Key |
| 微信支持 | 可直接爬取微信公众号文章（Jina/web_fetch 无法做到） |
| 图片保留 | 自动处理微信图片延迟加载（data-src -> src） |
| 代码块格式 | 自动转换为 ``` 格式 |

## 快速开始

### 1. 项目初始化

```bash
# 如果项目已存在，直接进入并激活虚拟环境
cd scrapling-html2text
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 如果是新项目，先创建
uv init scrapling-html2text
cd scrapling-html2text
uv venv
source .venv/bin/activate  # Linux/macOS
```

### 2. 安装依赖

```bash
# 使用 uv 安装依赖
uv add scrapling html2text playwright browserforge curl-cffi

# 安装 Playwright 浏览器
uv run playwright install chromium
```

### 3. 使用代码模板

完整代码见 templates/crawler.py

```python
from crawler import crawl_webpage

# 爬取微信公众号文章
crawl_webpage(
    "https://mp.weixin.qq.com/s/xxxxxx",
    output_file="article.md"
)
```

### 4. 运行爬虫

```bash
# 确保虚拟环境已激活，然后运行
python your_script.py
```

### 5. 使用完毕关闭虚拟环境

```bash
deactivate
```

## 文件结构

```
webpage-to-markdown/
├── SKILL                    # 本文件
├── templates/
│   └── crawler.py              # 完整代码模板（可直接使用）
├── examples/
│   └── wechat-output.txt       # 微信公众号输出示例
└── config/
    └── html2text-presets.py    # html2text 配置预设
```

## 使用场景

| 场景 | URL 示例 | 说明 |
|------|----------|------|
| 微信公众号 | mp.weixin.qq.com/s/... | 完美支持，图片+格式全保留 |
| 技术博客 | medium.com/@user/... | 绕过反爬，干净输出 |
| GitHub | github.com/user/repo | README 转 Markdown |
| Substack | substack.com/p/... | 绕过付费墙预览 |

## 方案对比

| 方案 | 微信公众号 | 反爬网站 | 每日限制 | 格式质量 |
|------|-----------|---------|---------|---------|
| **Scrapling + html2text** | 支持 | 支持 | 无限制 | 优秀 |
| Jina Reader | 不支持 | 部分支持 | 200次/天 | 优秀 |
| web_fetch | 不支持 | 不支持 | 无限制 | 差（全页噪音） |

## 配置说明

详见 config/html2text-presets.py

### 核心参数

| 参数 | 默认值 | 推荐值 | 说明 |
|------|--------|--------|------|
| `ignore_links` | True | **False** | 保留链接，AI 可追溯信息源 |
| `ignore_images` | True | **False** | 保留图片 URL |
| `body_width` | 78 | **0** | 设为 0 防止段落被截断 |
| `unicode_snob` | False | **True** | 使用 Unicode 避免乱码 |

### 预设模式

```python
from config.html2text_presets import create_converter

# full: 保留所有格式（推荐）
# clean: 仅保留文本和链接
# minimal: 纯文本模式
h = create_converter("full")
```

## 注意事项

1. **必须安装 Playwright 浏览器**: `playwright install chromium`
2. **必须使用 html2text**: 直接用 `get_all_text()` 会丢失所有格式
3. **微信公众号直接使用此方案**: 跳过 Jina，不浪费配额
4. **微信图片延迟加载**: 已自动处理 `data-src -> src` 转换
5. **代码块格式**: 已自动转换为 ``` 格式
6. **不要使用 mark_code**: 会生成 `[code]...[/code]` 格式

## 常见问题

### Q: 为什么不用 `get_all_text()`？

直接调用会丢失：段落结构、链接 URL、图片 URL、标题层级、列表格式

正确做法是先获取 `html_content`，再用 `html2text` 转换。

### Q: 遇到更复杂的反爬怎么办？

使用 Scrapling 的 `StealthyFetcher`：

```python
from scrapling import StealthyFetcher

fetcher = StealthyFetcher()
page = fetcher.get(url)
```

### Q: 如何处理微信图片？

已自动处理。微信使用 `data-src` 延迟加载，代码模板会自动转换为 `src`。

## 相关链接

- [Scrapling GitHub](https://github.com/D4Vinci/Scrapling)
- [html2text PyPI](https://pypi.org/project/html2text/)
- [Playwright 文档](https://playwright.dev/python/)
