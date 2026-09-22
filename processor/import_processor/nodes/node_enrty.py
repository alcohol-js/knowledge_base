# processor/import_processor/nodes/node_entry.py
from pathlib import Path

from processor.import_processor.base import BaseNode
from processor.import_processor.exceptions import FileProcessingError, ValidationError
from processor.import_processor.state import ImportGraphState
from processor.utils.file_util import file_util


class NodeEntry(BaseNode):
    """
    入口节点：任务分发
    """

    name = "node_entry"

    def process(self, state: ImportGraphState):

        # 1. 文件路径非空校验
        import_file_path = state.get("import_file_path")
        if not file_util.file_exist(import_file_path):
            raise FileProcessingError("文件不存在")
        # 2。 文件类型判断
        import_file_path_obj = Path(import_file_path)
        if import_file_path_obj.suffix == ".pdf":
            state["is_pdf_read_enabled"] = True
            state["pdf_path"] = import_file_path
        elif import_file_path_obj.suffix == ".md":
            state["is_md_read_enabled"] = True
            state["md_path"] = import_file_path
        else:
            raise ValidationError(message=f"该文件的后缀格式{import_file_path_obj.suffix}不支持")

        # 3， 提取标题
        state["file_title"] = import_file_path_obj.stem

        return state

    def get_name(self):
        """
        获取节点名称
        Returns:节点名称字符串

        """
        return "node_entry"