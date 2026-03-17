"""
html2text 配置预设

提供多种预设配置，适应不同的使用场景。

使用示例:
    from config.html2text_presets import create_converter

    # 使用完整格式预设（推荐）
    h = create_converter("full")
    markdown = h.handle(html_content)

    # 使用简洁格式预设
    h = create_converter("clean")
    markdown = h.handle(html_content)
"""

import html2text


def create_converter(preset: str = "full") -> html2text.HTML2Text:
    """
    创建 html2text 转换器

    Args:
        preset: 配置预设
            - "full": 保留所有格式（推荐用于 AI 内容处理）
            - "clean": 仅保留文本和链接
            - "minimal": 仅保留纯文本
            - "code": 适合代码密集的技术文章
            - "reading": 适合长文阅读，优化排版

    Returns:
        配置好的 HTML2Text 实例
    """
    h = html2text.HTML2Text()

    if preset == "full":
        # 保留所有格式（推荐用于 AI 内容处理）
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0
        h.unicode_snob = True
        h.pad_tables = True

    elif preset == "clean":
        # 仅保留文本和链接
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0
        h.unicode_snob = True

    elif preset == "minimal":
        # 纯文本模式
        h.ignore_links = True
        h.ignore_images = True
        h.ignore_emphasis = True
        h.body_width = 0

    elif preset == "code":
        # 适合代码密集的技术文章
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0
        h.unicode_snob = True
        h.pad_tables = True
        h.ignore_code_blocks = False

    elif preset == "reading":
        # 适合长文阅读，优化排版
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 80  # 限制行宽，提高可读性
        h.unicode_snob = True
        h.pad_tables = True
        h.wrap_links = True
        h.wrap_list_items = True

    else:
        raise ValueError(f"未知的预设: {preset}。可用预设: full, clean, minimal, code, reading")

    return h


# 参数说明
PARAMETERS = {
    "ignore_links": {
        "default": True,
        "recommended": False,
        "description": "是否忽略链接，设为 False 保留链接 URL"
    },
    "ignore_images": {
        "default": True,
        "recommended": False,
        "description": "是否忽略图片，设为 False 保留图片 URL"
    },
    "ignore_emphasis": {
        "default": True,
        "recommended": False,
        "description": "是否忽略强调格式（粗体/斜体）"
    },
    "body_width": {
        "default": 78,
        "recommended": 0,
        "description": "正文宽度，0 表示不自动换行"
    },
    "unicode_snob": {
        "default": False,
        "recommended": True,
        "description": "使用 Unicode 字符，避免乱码"
    },
    "ignore_tables": {
        "default": False,
        "recommended": False,
        "description": "是否忽略表格"
    },
    "pad_tables": {
        "default": False,
        "recommended": True,
        "description": "表格列填充对齐"
    },
    "single_line_break": {
        "default": False,
        "recommended": False,
        "description": "单换行符模式，False 使用双换行分隔段落"
    },
    "mark_code": {
        "default": False,
        "recommended": False,
        "description": "警告！设为 True 会生成 [code]...[/code] 格式，不是标准 Markdown"
    },
    "wrap_links": {
        "default": True,
        "recommended": False,
        "description": "是否换行链接，False 防止链接被截断"
    },
    "wrap_list_items": {
        "default": False,
        "recommended": False,
        "description": "是否换行列表项"
    },
    "default_image_alt": {
        "default": "",
        "recommended": "图片",
        "description": "默认图片 alt 文本"
    },
    "ul_item_mark": {
        "default": "-",
        "recommended": "-",
        "description": "无序列表标记符号"
    },
    "strong_mark": {
        "default": "**",
        "recommended": "**",
        "description": "强调（粗体）标记符号"
    },
    "emphasis_mark": {
        "default": "*",
        "recommended": "*",
        "description": "斜体标记符号"
    },
}


def print_parameters():
    """打印所有参数的说明"""
    print("html2text 参数配置参考")
    print("=" * 60)
    print(f"{'参数':<20} {'默认值':<10} {'推荐值':<10} {'说明'}")
    print("-" * 60)
    for name, info in PARAMETERS.items():
        default = str(info["default"])[:8]
        recommended = str(info["recommended"])[:8]
        desc = info["description"][:30]
        print(f"{name:<20} {default:<10} {recommended:<10} {desc}")


if __name__ == "__main__":
    print_parameters()
