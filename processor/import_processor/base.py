import logging
from abc import ABC, abstractmethod
from typing import Optional, TypeVar

from processor.import_processor.config import ImportConfig, get_config
from processor.import_processor.exceptions import ImportProcessError

T = TypeVar("T")  # 泛型状态类型

class BaseNode(ABC):

    """
    节点基类，实现节点通用功能
    """

    def __init__(self, config:Optional[ImportConfig] = None):
        self.config = config or get_config()
        self.node_name = self.get_name()
        self.logger = logging.getLogger(f"import.{self.node_name}")

    def __call__(self, state: T) ->T:
        try:
            self.logger.info(f"--- {self.node_name} 节点开始 ---")
            result = self.process(state)
            self.logger.info(f"--- {self.node_name} 节点完成 ---")
            return result
        except Exception as e:
            self.logger.error(f"{self.node_name} 节点执行失败: {e}")
            raise ImportProcessError(
                message="节点执行失败",
                node_name = self.node_name,
                cause=e
            )

    @abstractmethod
    def process(self, state: T) -> T:
        """
        节点核心处理逻辑,由子节点重写
        Args:
            state:图状态字典

        Returns:
            更新后的状态字典
        """

    @abstractmethod
    def get_name(self):
        """
        获取节点名称
        Returns:节点名称字符串

        """
        pass

    def log_step(self, step_name: str, message: str = ""):
        """
        记录步骤日志
            [步骤名称]传递进来的消息
        Args:
            step_name: 步骤名称
            message: 附加信息
        """
        log_msg = f"[{step_name}]"
        if message:
            log_msg += f" {message}"
        self.logger.info(log_msg)


# 配置日志格式
def setup_logging(level: int = logging.INFO):
    """
    配置日志格式

    Args:
        level: 日志级别
    """

    logger = logging.getLogger()
    logger.setLevel(level)

    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',  # INFO 显示为绿色
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))

    logger.handlers.clear()
    logger.addHandler(handler)