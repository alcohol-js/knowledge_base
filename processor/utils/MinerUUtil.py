import logging
import time
from pathlib import Path
from time import sleep

import requests

from processor.import_processor.exceptions import PdfConversionError

logger = logging.getLogger(__name__)
class MinerUUtil:

    @staticmethod
    def get_file_upload(path: Path, token: str)->str:
        """
        上传解析文件
        :param path: 需要解析的本地文件path对象
        :param token: api token
        :return: batch_id
        """
        url = "https://mineru.net/api/v4/file-urls/batch"
        header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "files": [
                {"name":f"{path.name}"}
            ],
            "model_version":"vlm"
        }
        file_path = [path]
        try:
            response = requests.post(url,headers=header,json=data)
            if response.status_code == 200:
                result = response.json()

                if result["code"] == 0:
                    batch_id = result["data"]["batch_id"]
                    urls = result["data"]["file_urls"]
                    logger.info("获取上传文件链接成功，batch_id:{} | urls:{}".format(batch_id, urls))
                    if len(urls) <= 0:
                        raise

                    for i in range(0, len(urls)):
                        with open(file_path[i], 'rb') as f:
                            res_upload = requests.put(urls[i], data=f)
                            if res_upload.status_code == 200:
                                logger.info(f"{file_path[i].name}上传成功")
                            else:
                                logger.error(f"{file_path[i].name}上传失败")
                                raise PdfConversionError("文件上传minerU服务器失败")

                    return str(batch_id)
                else:
                    logger.error("获取上传文件链接失败")
                    raise PdfConversionError("获取上传文件链接失败")
            else:
                logger.error(f"获取上传文件链接请求失败，code:{response.status_code}")
                raise PdfConversionError("获取上传文件链接请求失败")
        except Exception as err:
            logger.error(f"文件上传minerU服务器异常")
            raise

    @staticmethod
    def get_file_analysis_result_poll(batch_id:str, token:str, poll_time, max_time, req_time) ->str:
        """
        轮询获取任务解析是否成功
        :param batch_id: 任务id
        :param token: api token
        :param poll_time: 轮询间隔时间(s)
        :param max_time: 最大轮询时间(s)
        :param req_time: 单次请求最大耗时(s)
        :return:
        """

        start_time = time.time()

        while True:
            if(time.time() - start_time) > max_time:
                break

            link = 0
            try:
                link += 1
                url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
                header = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                }

                res = requests.get(url, headers=header, timeout=req_time)
                if res.status_code != 200 or res.json()["code"] != 0:
                    raise

                data = res.json()["data"][0]


                if data["state"] != "done":
                    logger.debug(f"第{link}次轮询结果未完成")
                    sleep(poll_time)
                    continue

                return str(data["full_zip_url"])
            except Exception as err:
                logger.debug(f"第{link}次轮询请求异常")

        raise PdfConversionError("minerU解析图片超时")

    @staticmethod
    def get_zip(url:str,output_dir: str, file_name:str):
        """
        下载解析结果
        :param url: 解析结果下载地址
        :param output_dir: 压缩包输出路径
        :param file_name: 压缩包输出名称
        """
        # url判空
        if not url or not output_dir:
            raise PdfConversionError("解析结果下载链接为空")

        try:
            # 下载解析结果
            logger.info("开始下载压缩包")
            resp = requests.get(url)
            if resp.status_code != 200:
                raise PdfConversionError("下载解析结果请求异常")

            zip_save_path = Path(output_dir) / f"{file_name}_result.zip"
            with open(zip_save_path, "wb") as f:
                f.write(resp.content)
            logger.info("压缩文件下载成功")
        except Exception as err:
            logger.error("下载解析结果失败")
            raise

