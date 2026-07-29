import requests
import os
from urllib.request import urlretrieve
import json
from config.config import *
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# 构造url
params = {
    "limit": 1,
    "page": 1
}

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
            logger.error(f"JSON 解析失败: {e}, 响应内容前100字符: {response.text[:100]}")
            return []

        if isinstance(response, list):
            return response.json()
        else:
            logger.warning(f"未知的响应格式: {type(response)}")

    except requests.exceptions.Timeout:
        logger.error(f"请求超时 (超过 {timeout} 秒)")
        return []

    except requests.exceptions.ConnectionError:
        logger.error("网络连接失败，请检查网络或代理设置")
        return []

    except requests.exceptions.HTTPError as e:
        status = response.status_code
        if status == 421:
            logger.error("请求频率过高，被服务器限流 (User Throttled)，请稍后再试")
        elif status == 404:
            logger.error("请求的资源不存在 (404)")
        elif status == 403:
            logger.error("权限不足，访问被拒绝 (403)")
        else:
            logger.error(f"HTTP 错误 {status}: {e}")
        return []

    except requests.exceptions.RequestException as e:
        logger.error(f"请求发生未知错误: {e}")
        return []


# open_tag_library
if os.path.getsize(tag_library_dir / tag_library_name) == 0:
            tag_library = {}
else: 
    with open(tag_library_dir / tag_library_name, 'r', encoding='utf-8') as f:
        tag_library = json.load(f)


def download_single_image(post_data, download_dir):
    """
    下载单张图片，返回保存的文件名
    """
    image_url = post_data['jpeg_url']
    image_id = post_data['id']
    file_extension = os.path.splitext(image_url)[1]     # 文件扩展名
    file_name = f"{image_id}{file_extension}"
    file_path = download_dir / file_name

    # 下载图片
    urlretrieve(image_url, file_path)
    return file_name


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
            updates[tag] = 0
    return updates


with open(tag_library_dir / tag_library_name, 'w', encoding='utf-8') as f:
    json.dump(tag_library, f, indent=4, ensure_ascii=False)


def process_one_post(post_data, tag_library, download_dir):
    """
    处理一张图片：下载 → 评价 → 更新标签库
    """
    # 下载图片
    download_single_image(post_data, download_dir)

    # 获取标签
    tags_str = post_data.get('tags', '')

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
    pass