import sys

from mod.project.docker.app.gpu import nvidia

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')

import public

def gpu_class():
    return 'nvidia'


class main:
    def __init__(self):
        self.driver = None
        if gpu_class() == 'nvidia':
            self.driver = nvidia.NVIDIA()
        # elif gpu_class() == 'amd':
        #     self.driver = amd.AMD()

    def get_all_device_info(self, get):
        """
        获取所有gpu信息
        Args:
            get:

        Returns:
            dict: All gpu information are included.
        """
        public.print_log('gpu info')
        if not self.driver.support:
            return public.returnResult(True, data={})
        return public.returnResult(True, data=self.driver.get_all_device_info())

    def get_info_by_index(self, get):
        """
        返回驱动信息
        Args:
            get:

        Returns:

        """
        index = 0
        if not self.driver.support:
            return public.returnResult(True, data={})
        try:
            index = int(get.index)
        except ValueError as e:
            public.returnResult(False, "{} need an int: {}".format(self.get_info_by_index.__name__, e))
        return public.returnResult(True, data=self.driver.get_info_by_index(index))

    def get_system_info(self, get):
        """
        返回驱动信息
        Args:
            get:

        Returns:

        """
        if not self.driver.support:
            return public.returnResult(True, data={})
        return public.returnResult(True, data=self.driver.get_system_info())
