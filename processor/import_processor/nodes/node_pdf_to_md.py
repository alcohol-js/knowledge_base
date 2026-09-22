# processor/import_processor/nodes/node_pdf_to_md.py
import shutil
import zipfile
from pathlib import Path

from openai.types.beta.beta_response_function_shell_tool_call_output import Output

from processor.import_processor.base import BaseNode
from processor.import_processor.state import ImportGraphState
from processor.utils.file_util import file_util
from processor.utils.MinerUUtil import MinerUUtil


class NodePDFToMD(BaseNode):
    """
    PDF 转 Markdown 节点：PDF结构化解析
    """

    name = "node_pdf_to_md"

    def process(self, state: ImportGraphState):

        if not state.get("is_pdf_read_enabled"):
            self.logger.error("图状态异常")
            raise
        pdf_path = state.get("pdf_path")
        output_path = state.get("file_dir")
        # 1. 文件路径判空
        file_util.file_exist(pdf_path)

        # 2. 上传文件到mineru服务器
        pdf_path_obj = Path(pdf_path)
        batch_id = MinerUUtil.get_file_upload(pdf_path_obj, self.config.minerU_token)

        # 3. 轮询mineru解析结果
        zip_url = MinerUUtil.get_file_analysis_result_poll(batch_id, self.config.minerU_token, 3, 30, 3)

        # 4. 结果下载与解压
        file_name = state.get("file_title")
        MinerUUtil.get_zip(zip_url, output_path, file_name)
        mir_path_obj = Path(output_path) / file_name

        if mir_path_obj.exists():
            shutil.rmtree(mir_path_obj)

        with zipfile.ZipFile(Path(output_path) / f"{file_name}_result.zip", "r") as f:
            f.extractall(mir_path_obj)

        # 5. 重命名文件以及状态参数填充
        file_path = mir_path_obj / "full.md"
        new_name = file_path.with_name(f"{file_name}.md")
        file_path.rename(new_name)
        state["md_path"] = str(file_path.resolve())



        return state

    def get_name(self):
        """
        获取节点名称
        Returns:节点名称字符串

        """
        return self.name