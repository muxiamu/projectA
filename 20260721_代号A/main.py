import requests
import os
from urllib.request import urlretrieve
import json
from config.config import *


# 构造url
page = 1
limit = 1
yande_url = yande_url + f"page={page}&limit={limit}"


# 请求回应
response = requests.get(url=yande_url)
json_data = response.json()


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