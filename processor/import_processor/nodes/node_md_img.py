# processor/import_processor/nodes/node_md_img.py
from pathlib import Path

from processor.import_processor.base import BaseNode
from processor.import_processor.exceptions import ImageProcessingError
from processor.import_processor.state import ImportGraphState
from processor.utils.file_util import file_util


class NodeMDImg(BaseNode):
    """
    MarkDown图片处理节点：多模态图片理解
    """

    name = "node_md_img"

    def process(self, state: ImportGraphState):
        md_path = state["md_path"]

        if not file_util.file_exist(md_path):
            self.logger.error("md路径信息错误")
            raise ImageProcessingError("md路径信息错误")

        md_path_obj = Path(md_path)
        with open(md_path_obj, "r") as f:
            content = f.read()

        state["md_content"] = content


        return state

    def get_name(self):
        """
        获取节点名称
        Returns:节点名称字符串

        """
        return self.name