import logging
from pathlib import Path
from datetime import datetime
from config.config import log_dir


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