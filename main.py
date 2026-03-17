import html2text
import re
from scrapling import Fetcher


def _convert_code_blocks_to_fenced(text: str) -> str:
    """将缩进代码块转换为 ``` 格式"""
    lines = text.split('\n')
    result = []
    in_code_block = False
    code_buffer = []

    # 列表项的模式（微信特殊格式：4空格 + 数字 + 点 + 多空格）
    # 匹配: "    1.   ", "    2.  ", "- ", "* "
    list_pattern = re.compile(r'^\s*[0-9]+\.\s+|^[-*+]\s')

    for i, line in enumerate(lines):
        # 检测缩进代码块（4个空格开头）
        is_indented = line.startswith('    ')
        # 判断是否是列表项
        is_list_item = bool(list_pattern.match(line))

        if is_indented and not is_list_item:
            if not in_code_block:
                in_code_block = True
                code_buffer = []
            # 移除前导4空格
            code_buffer.append(line[4:] if len(line) > 4 else '')
        else:
            if in_code_block:
                # 结束代码块
                if code_buffer:
                    # 过滤掉只有空行的代码块
                    non_empty = [c for c in code_buffer if c.strip()]
                    if non_empty:
                        result.append('```')
                        result.extend(code_buffer)
                        result.append('```')
                        result.append('')
                    else:
                        result.extend([''] * len(code_buffer))
                in_code_block = False
                code_buffer = []
            result.append(line)

    # 处理末尾的代码块
    if in_code_block and code_buffer:
        non_empty = [c for c in code_buffer if c.strip()]
        if non_empty:
            result.append('```')
            result.extend(code_buffer)
            result.append('```')
        else:
            result.extend([''] * len(code_buffer))

    return '\n'.join(result)


def crawl_wechat_article(url: str, output_file: str = "article.md") -> str:
    """爬取微信公众号文章并转换为Markdown格式"""
    # 使用 scrapling 的 Fetcher 爬取页面
    fetcher = Fetcher()
    page = fetcher.get(url)

    # 获取文章标题
    title_elems = page.css("#activity-name")
    title = title_elems[0].get_all_text().strip() if title_elems else "无标题"

    # 获取作者/公众号名称
    author_elems = page.css("#js_name")
    author = author_elems[0].get_all_text().strip() if author_elems else "未知作者"

    # 获取发布时间
    time_elems = page.css("#publish_time")
    publish_time = time_elems[0].get_all_text().strip() if time_elems else ""

    # 获取文章正文内容 (微信公众号文章内容在 #js_content 中)
    content_elems = page.css("#js_content")

    if not content_elems:
        print("未能获取到文章内容")
        return ""

    content_elem = content_elems[0]

    # 获取文章HTML
    content_html = content_elem.html_content

    # 预处理：修复微信图片延迟加载问题（data-src -> src）
    content_html = re.sub(
        r'<img([^>]*?)data-src=["\']([^"\']+)["\']([^>]*?)>',
        r'<img\1src="\2"\3>',
        content_html
    )
    # 同时处理 data-type="png" 等属性，确保图片能被识别
    content_html = re.sub(
        r'<img([^>]*?)data-type=["\'][^"\']+["\']([^>]*?)>',
        r'<img\1\2>',
        content_html
    )

    # 使用 html2text 转换为 Markdown
    h = html2text.HTML2Text()

    # 核心配置（推荐）
    h.ignore_links = False          # 保留链接
    h.ignore_images = False         # 保留图片
    h.ignore_emphasis = False       # 保留强调格式（粗体/斜体）
    h.body_width = 0                # 不自动换行（重要！防止段落被截断）
    h.unicode_snob = True           # 使用 Unicode 字符（避免乱码）
    # 注意：mark_code 会生成 [code]...[/code] 格式，不是标准 markdown
    # h.mark_code = True            # 不推荐，会破坏代码块格式
    h.pad_tables = True             # 表格填充对齐

    markdown_content = h.handle(content_html)

    # 后处理：将缩进代码块转换为 ``` 格式
    markdown_content = _convert_code_blocks_to_fenced(markdown_content)

    # 组装完整的Markdown文档
    full_markdown = f"""# {title}

**作者**: {author}
**发布时间**: {publish_time}
**原文链接**: {url}

---

{markdown_content}
"""

    # 保存到文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_markdown)

    print(f"文章已保存到: {output_file}")
    return full_markdown


def main():
    url = "https://mp.weixin.qq.com/s/EwVItQH4JUsONqv_Fmi4wQ"
    crawl_wechat_article(url)


if __name__ == "__main__":
    main()
