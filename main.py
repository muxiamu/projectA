import requests
import os
from urllib.request import urlretrieve
import json
from config.config import *
import logging


logger = logging.getLogger(__name__)


# 构造url
params = {
    "limit": 1,
    "page": 1
}

# 请求回应
try:
    response = requests.get(url=yande_url, params=params, timeout=timeout)
    response.raise_for_status()
    try:
        json_data = response.json()
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}, 响应内容前100字符: {response.text[:100]}")
        json_data = []

    if isinstance(json_data, list):
        pass
    else:
        logger.warning(f"未知的响应格式: {type(json_data)}")

except requests.exceptions.Timeout:
    logger.error(f"请求超时 (超过 {timeout} 秒)")
    json_data = []

except requests.exceptions.ConnectionError:
    logger.error("网络连接失败，请检查网络或代理设置")
    json_data = []

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
    json_data = []

except requests.exceptions.RequestException as e:
    logger.error(f"请求发生未知错误: {e}")
    json_data = []

# 获取下载链接和标签
if os.path.getsize(tag_library_dir / tag_library_name) == 0:
        tag_library = {}
else: 
    with open(tag_library_dir / tag_library_name, 'r', encoding='utf-8') as f:
        tag_library = json.load(f)
for current_post in json_data:
    image_url = current_post['jpeg_url']
    image_id = current_post['id']
    image_tags = current_post['tags']
    file_extension = os.path.splitext(image_url)[1]     # 文件扩展名
    file_name = os.path.join(f"{image_id}{file_extension}")


    # 下载图片
    urlretrieve(image_url, download_dir / file_name)

    # 评价
    evaluate = input('Like or dislike?(y or n)')

    # 更新标签库
    tag_list = image_tags.split()
    
    for tag in tag_list:
        if tag not in tag_library:
            tag_library[tag] = 0
        if evaluate == 'y':
            tag_library[tag] += 1
        elif evaluate == 'n':
            tag_library[tag] -= 1
        else:
            pass
with open(tag_library_dir / tag_library_name, 'w', encoding='utf-8') as f:
    json.dump(tag_library, f, indent=4, ensure_ascii=False)