# processor/import_processor/nodes/node_md_img.py
import base64
import os
import re
import time
from collections import deque
from pathlib import Path
from typing import Deque, Tuple

from langchain_openai import ChatOpenAI

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

        # 1. 校验md文档路径、获取文档内容
        md_path = state["md_path"]

        if not file_util.file_exist(md_path):
            self.logger.error("md路径信息错误")
            raise ImageProcessingError("md路径信息错误")

        md_path_obj = Path(md_path)
        with open(md_path_obj, "r") as f:
            content = f.read()

        state["md_content"] = content

        # 2. 遍历图片目录，获取合法图片及上下文
        img_path = md_path_obj.parent / "images"
        img_msg = self.scan_images(content, img_path)

        # 3. 调用视觉模型，获取图片摘要
        self._step_3_generate_summaries(md_path_obj.stem, img_msg)

        # 4. 上传图片，获取上传链接，替换md文档图片链接和摘要

        # 5. 保存新md文档

        return state

    def scan_images(self, content: str, img_path: Path)->list:
        list = []
        for image_file in os.listdir(img_path):
            file_ext = os.path.splitext(image_file)[1]

            if file_ext not in self.config.get("image_extensions"):
                continue

            # 判断图片是否在md中被引用
            pattern = re.compile(r"!\[.*?\]\(.*?" + re.escape(image_file) + r".*?\)")
            match = pattern.search(content)
            if not match:
                continue

            # 3、截取匹配位置的上文和下文（防止索引越界）
            start, end = match.span()
            context_len = 100
            pre_text = content[max(0, start - context_len):start]
            post_text = content[end:min(len(content), end + context_len)]

            msg = {
                "file_name": image_file,
                "file_path": str(img_path / image_file),
                "pre_context": pre_text,
                "post_context": post_text
            }
            list.append(msg)

        return list

    def _step_3_generate_summaries(self, doc_stem: str, target_images: list):
        """
        步骤3：批量为待处理图片生成内容摘要，带API速率限制防止触发大模型限流
        :param doc_stem: 文档文件名（不含后缀），作为大模型prompt上下文
        :param targets: 待处理图片列表，元素为(图片文件名, 图片完整路径, 图片上下文)
        :param requests_per_minute: 每分钟最大API请求数，默认9次（按大模型限制调整）
        :return: 图片摘要字典，键：图片文件名，值：图片内容摘要
        """
        summaries = {}

        # 1、外部初始化双端队列，用于API速率限制，跨循环复用
        request_deque = deque()

        # 2、循环处理图片
        for item in target_images:
            img_file = item.get("file_name")
            image_path = item.get("file_path")
            context = (item.get("pre_context"), item.get("post_context"))
            # 2.1、速率限制
            self._apply_api_rate_limit(request_deque, max_requests=10)

            # 2.2、调用大模型生成图片摘要
            self._summarize_image(image_path, doc_stem, context, item)

        return summaries

    def _apply_api_rate_limit(
            self,
            request_times: Deque[float],
            max_requests: int,
            window_seconds: int = 60
    ) -> None:
        """
        通用滑动窗口API速率限制器（抽离为公共工具）
        核心逻辑：维护请求时间戳双端队列，窗口内请求数超上限则自动等待，防止触发第三方API限流
        :param request_times: 存储请求时间戳的双端队列，需外部初始化（全局/单例），跨调用复用
        :param max_requests: 速率限制窗口内的最大允许请求次数
        :param window_seconds: 速率限制滑动窗口时长，默认60秒（1分钟）
        :return: None，超出限制时会阻塞等待
        """
        current_time = time.time()

        # 1. 清理滑动窗口外的过期请求时间戳，保证队列仅存窗口内的请求
        while request_times and current_time - request_times[0] >= window_seconds:
            request_times.popleft()

        # 2. 窗口内请求数达上限，计算并阻塞等待剩余时间
        if len(request_times) >= max_requests:
            # 计算需要等待的时长（窗口总时长 - 最早请求已存在的时长）
            sleep_duration = window_seconds - (current_time - request_times[0])
            if sleep_duration > 0:
                self.logger.info(
                    f"触发API速率限制，窗口{window_seconds}秒内最多{max_requests}次，需等待：{sleep_duration:.2f} 秒")
                time.sleep(sleep_duration)
                # 等待后更新当前时间，重新清理过期请求（避免等待期间有请求过期）
                current_time = time.time()
                while request_times and current_time - request_times[0] >= window_seconds:
                    request_times.popleft()

        # 3. 记录当前请求时间戳，加入滑动窗口队列
        request_times.append(current_time)
        self.logger.info(f"API请求时间戳已记录，当前{window_seconds}秒窗口内请求数：{len(request_times)}")

    def _summarize_image(self, image_path: str, root_folder: str, image_content: Tuple[str, str], item:dict) -> str:
        """
           调用多模态大模型总结图片内容。

           参数：
           - image_path: 图片本地路径。
           - root_folder: 文档所属文件夹名（提供更多上下文）。
           - image_content: 图片在文档中的上下文 (前文, 后文)。
        """
        with open(image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode("utf-8")

        try:
            chat_model = ChatOpenAI(
                model=self.config.vl_model,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                temperature=self.config.llm_temperature
            )
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""这是"{root_folder}"文件中的一张图片，图片上文部分为"{image_content[0]}"，下文部分为"{image_content[1]}"，请用中文简要总结这张图片的内容，用于 Markdown 图片标题。"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            response = chat_model.invoke(messages)
            item["abstract"] = response.content.strip().replace("\n", "")

        except Exception as e:
            self.logger.error(f"图像总结失败：{image_path}, 错误{e}")
            item["abstract"] = "图片描述"


    def get_name(self):
        """
        获取节点名称
        Returns:节点名称字符串

        """
        return self.name