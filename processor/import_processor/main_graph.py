from langgraph.constants import START, END
from langgraph.graph import StateGraph

from processor.import_processor.nodes.node_bge_embedding import NodeBGEEmbedding
from processor.import_processor.nodes.node_document_split import NodeDocumentSplit
from processor.import_processor.nodes.node_enrty import NodeEntry
from processor.import_processor.nodes.node_import_milvus import NodeImportMilvus
from processor.import_processor.nodes.node_item_name_recognition import NodeItemNameRecognition
from processor.import_processor.nodes.node_md_img import NodeMDImg
from processor.import_processor.nodes.node_pdf_to_md import NodePDFToMD
from processor.import_processor.state import ImportGraphState


class KBImportWorkflow:
    """
    知识库导入工作流
    """

    def __init__(self, config = None):
        self.__compiled_graph = None

    def build_graph(self):
        # 1. 初始化图
        graph = StateGraph(ImportGraphState);

        # 2. 注册节点到工作流
        graph.add_node("node_entry", NodeEntry())
        graph.add_node("node_pdf_to_md", NodePDFToMD())
        graph.add_node("node_md_img", NodeMDImg())
        graph.add_node("node_document_split", NodeDocumentSplit())
        graph.add_node("node_item_name_recognition", NodeItemNameRecognition())
        graph.add_node("node_bge_embedding", NodeBGEEmbedding())
        graph.add_node("node_import_milvus", NodeImportMilvus())

        # 3. 构建边
        graph.add_edge(START, "node_entry")

        graph.add_conditional_edges("node_entry", self.route_after_entry,
                                    {
                                        #key：路由函数的返回值，value:节点的名字
                                        "node_md_img": "node_md_img",
                                        "node_pdf_to_md": "node_pdf_to_md",
                                        END: END
                                    });

        graph.add_edge("node_pdf_to_md", "node_md_img");
        graph.add_edge("node_md_img", "node_document_split")
        graph.add_edge("node_document_split", "node_item_name_recognition")
        graph.add_edge("node_item_name_recognition", "node_bge_embedding")
        graph.add_edge("node_bge_embedding", "node_import_milvus")
        graph.add_edge("node_import_milvus", END)

        return graph.compile()

    @staticmethod
    def route_after_entry(state: ImportGraphState)-> str:

        if state.get("is_pdf_read_enabled"):
            return "node_pdf_to_md"
        elif state.get("is_md_read_enabled"):
            return "node_md_img"
        else:
            return END

    @property
    def graph(self):
        if self.__compiled_graph is None:
            self.__compiled_graph = self.build_graph()
        return self.__compiled_graph


    def run(self, state: ImportGraphState, stream: bool = False):
        """
        统一执行入口，支持切换invoke/stream
        :param state: 初始状态
        :param stream: 是否流式输出
        :return: 执行结果
        """
        if stream:
            return self.graph.stream(state, stream_mode="values")
        else:
            return self.graph.invoke(state)

if __name__ == "__main__":
    graph = KBImportWorkflow()
    graph.graph.get_graph().print_ascii()
