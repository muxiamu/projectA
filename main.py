from config.config import tag_library_dir, tag_library_name, download_dir
from core.api_client import download_single_image, request_response
from core.tag_manager import calculate_tag_updates, load_tags_library, save_tags_library
from core.evaluator import ask_for_evaluate
from core.logger import logger
from ui.main_window import App


def process_one_post(post_data, tag_library, download_dir):
    """
    处理一张图片：下载 → 评价 → 更新标签库
    """
    # 下载图片
    file_name = download_single_image(post_data, download_dir)
    # 下载失败跳过本轮
    if file_name is None:
        return tag_library

    # 获取标签
    tags_str = post_data.get('tags')

    # 询问评价
    is_liked = ask_for_evaluate()

    # 计算更新
    updates = calculate_tag_updates(tags_str, is_liked)

    # 应用到标签库
    for tag, delta in updates.items():
        tag_library[tag] = tag_library.get(tag, 0) + delta

    # 返回更新后的库
    return tag_library


if __name__ == "__main__":
    logger.info("🚀 程序启动，正在加载图形界面...")
    # 创建 App 实例，App 内部会自动加载标签库
    app = App()
    # 进入 Tkinter 主事件循环（程序将在这里等待用户操作）
    app.mainloop()
    logger.info("👋 程序正常退出")