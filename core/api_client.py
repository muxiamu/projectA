import requests
import json
from config.config import yande_url, timeout, max_retry, chunk_size
import time
import os
from pathlib import Path
from core.logger import logger


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