import os


class file_util:

    @staticmethod
    def file_exist(path: str | None) -> bool:

        # 判断路径字符串是否为空
        if not path or not os.path.exists(path):
            return False
        return True