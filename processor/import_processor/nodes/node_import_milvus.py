# processor/import_processor/nodes/node_import_milvus.py

from processor.import_processor.base import BaseNode
from processor.import_processor.state import ImportGraphState


class NodeImportMilvus(BaseNode):
    """
    导入向量库节点：数据持久化
    """

    name = "node_import_milvus"

    def process(self, state: ImportGraphState):

        return state

    def get_name(self):
        """
        获取节点名称
        Returns:节点名称字符串

        """
        pass