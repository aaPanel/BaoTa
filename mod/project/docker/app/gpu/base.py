from abc import ABC, abstractmethod


class GPUBase(ABC):
    name = 'base'
    support = None
    @abstractmethod
    def _get_mem_info(self, *args, **kwargs):
        """
        获取显存占用
        Returns:

        """
        pass

    @abstractmethod
    def _get_clock_info(self, *args, **kwargs):
        """
        获取时钟信息
        Returns:

        """

        pass

    @abstractmethod
    def _get_temp_info(self, *args, **kwargs):
        """
        获取温度
        Returns:

        """
        pass

    @abstractmethod
    def _get_uti_info(self, *args, **kwargs):
        """
        获取占用


        Returns:

        """
        pass

    @abstractmethod
    def _get_proc_uti(self, *args, **kwargs):
        """
        获取进程占用
        Returns:

        """
        pass

    @abstractmethod
    def _get_fan_info(self, *args, **kwargs):
        pass

    @abstractmethod
    def _get_device_name(self, *args, **kwargs):
        pass

    @abstractmethod
    def _get_device_version(self, *args, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def is_support(cls):
        pass