# processor/import_processor/nodes/node_item_name_recognition.py

from processor.import_processor.base import BaseNode
from processor.import_processor.state import ImportGraphState


class NodeItemNameRecognition(BaseNode):
    """
    主体识别节点：主体识别与标签提取
    """

    name = "node_item_name_recognition"

    def process(self, state: ImportGraphState):

        return state

    def get_name(self):
        """
        获取节点名称
        Returns:节点名称字符串

        """
        pass