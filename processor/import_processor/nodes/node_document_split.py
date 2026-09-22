# processor/import_processor/nodes/node_document_split.py

from processor.import_processor.base import BaseNode
from processor.import_processor.state import ImportGraphState


class NodeDocumentSplit(BaseNode):
    """
    文档切分节点：智能文档切片
    """

    name = "node_document_split"

    def process(self, state: ImportGraphState):


        return state

    def get_name(self):
        """
        获取节点名称
        Returns:节点名称字符串

        """
        pass