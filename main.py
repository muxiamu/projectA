import requests
import os
from urllib.request import urlretrieve
import json
from config.config import *
import logging
from pathlib import Path
import time
from datetime import datetime

def init_logger():
    """
    初始化日志配置
    """
    # 构造日志路径
    timestamp = datetime.now().strftime(r"%Y-%m-%d_%H-%M-%S")
    log_file_name = f"{timestamp}.log"
    log_file_path = Path(log_dir) / log_file_name

    # 创建日志文件夹
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"日志文件已创建: {log_file_path}")
    return logger

logger = init_logger()


def request_response(params):
    """
    请求图像列表    
    返回json格式的回应
    """
    try:
        response = requests.get(url=yande_url, params=params, timeout=timeout)
        response.raise_for_status()
        try:
            response = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"错误：JSON 解析失败: {e}, 响应内容前100字符: {response.text[:100]}")
            return []

        if isinstance(response, list):
            return response
        else:
            logger.warning(f"警告：未知的响应格式: {type(response)}")
            return []

    except requests.exceptions.Timeout:
        logger.error(f"错误：请求超时 (超过 {timeout} 秒)！")
        return []

    except requests.exceptions.ConnectionError:
        logger.error("错误：网络连接失败，请检查网络或代理设置！")
        return []

    except requests.exceptions.HTTPError as e:
        status = response.status_code
        if status == 421:
            logger.error("错误：请求频率过高，被服务器限流 (User Throttled)，请稍后再试！")
        elif status == 404:
            logger.error("错误：请求的资源不存在 (404)！")
        elif status == 403:
            logger.error("错误：权限不足，访问被拒绝 (403)！")
        else:
            logger.error(f"错误：HTTP 错误 {status}: {e}")
        return []

    except requests.exceptions.RequestException as e:
        logger.error(f"错误：请求发生未知错误: {e}")
        return []


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


def download_single_image(post_data, download_dir):
    """
    下载单张图片，返回保存的文件名
    """
    image_url = post_data['jpeg_url']
    image_id = post_data['id']
    file_extension = os.path.splitext(image_url)[1]     # 文件扩展名
    file_name = f"{image_id}{file_extension}"
    file_path = Path(download_dir) / file_name

    for i in range(max_retry):
        # 下载图片
        try:
            response = requests.get(image_url, stream=True, timeout=timeout)
            response.raise_for_status()

            # 流式下载
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

            logger.debug(f"{file_name}下载完成!")
            return file_name
        
        except requests.exceptions.Timeout:
            if i < max_retry -1:
                wait = 1 + max_retry
                logger.warning(f"{file_name}下载超时，{wait}秒后重试，尝试{i +1} / {max_retry}!")
                time.sleep(wait)
            else:
                logger.error(f"{file_name}重试{max_retry}次仍然超时，下载失败!")
                return None
                
        except requests.exceptions.ConnectionError:
            if i < max_retry -1:
                wait = 1 + i
                logger.warning(f"{file_name}网络断开，{wait}秒后重试，尝试{i +1} / {max_retry}!")
                time.sleep(wait)
            else:
                logger.error(f"{file_name}重试{max_retry}次仍然网络异常，下载失败!")
                return None

        except Exception as e:
            # 删除残留
            if file_path.exists():
                file_path.unlink()
            logger.error(f"{file_name}下载失败: {e}！")
            return None


def ask_for_evaluate():
    """
    询问用户对当前图片的评价      
    返回: True (喜欢), False (不喜欢), 或 None (无效输入)
    """
    while True:
        choice = input('Like or dislike?(y/n):').strip().lower()
        if choice == 'y':
            return True
        elif choice == 'n':
            return False
        else:
            print('请输入y或n')


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
    # 构造url
    params = {
        "limit": 1,
        "page": 1
    }

    # 加载标签库
    tags_library = load_tags_library(tag_library_dir, tag_library_name)

    # 请求回应
    response = request_response(params)

    # 处理回应
    for post_data in response:
        tags_library = process_one_post(post_data, tags_library, download_dir)
        save_tags_library(tag_library_dir, tag_library_name, tags_library)

    # 更新库文件
    save_tags_library(tag_library_dir, tag_library_name, tags_library)