# 配置文件
from pathlib import Path

#----------------------路径配置----------------------
# 根目录
base_dir = Path(__file__).parent.parent.resolve()

# 下载图片的存放目录
download_dir = base_dir / "downloads"

# 标签库 JSON 文件
tag_library_name = "tag_library.json"
tag_library_dir = base_dir / "tag_library"

# 日志文件存放位置
log_dir = base_dir / "log"


#----------------------API配置----------------------
# yande API
yande_url = r"https://yande.re/post.json"
timeout = 60        # 请求超时时间


#----------------------下载配置----------------------
max_retry = 3           # 最大重试次数
chunck_size = 8192      # 流式下载块大小


#----------------------系统参数----------------------
default_tag_score = 0   # 新标签的默认分数
score_step = 0.2        # 用户每次打分影响标签的步长


download_dir.mkdir(parents=True, exist_ok=True)
tag_library_dir.mkdir(parents=True, exist_ok=True)
log_dir.mkdir(parents=True, exist_ok=True)