from pathlib import Path
import json
from core.logger import logger


def load_tags_library(tag_library_dir, tag_library_name):
    """
    加载标签库  
    """
    file_path = Path(tag_library_dir) / tag_library_name

    if not file_path.exists():
        return {}
    if file_path.stat().st_size == 0:
        return {}

    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                logger.info(f"标签库加载成功，共{len(data)}个标签！")
                return data
            else:
                logger.warning(f"警告：{file_path}格式错误，已重置！")
                return {}
            
    except json.JSONDecodeError as e:
        logger.warning(f"警告:{file_path}已损坏{e}，已重置！")
        return {}


def save_tags_library(tag_library_dir, tag_library_name, tag_library):
    """
    保存标签库到 JSON 文件
    """
    file_path = Path(tag_library_dir) / tag_library_name
    try:
        # 创建库文件夹
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tag_library, f, indent=4, ensure_ascii=False)
        logger.info(f"标签库已保存至{file_path}")

    except Exception as e:
        logger.warning(f"标签库保存失败: {e}")


def calculate_tag_updates(tag_str, is_liked):
    """
    根据评价更新标签权重    
    参数：tags_str, is_liked    
    返回：字典{tags_str:1}
    """
    tag_list = tag_str.split()
    updates = {}
    for tag in tag_list:
        # 如果喜欢+1，不喜欢-1
        if is_liked:
            updates[tag] = 1
        else:
            updates[tag] = -1   
    return updates