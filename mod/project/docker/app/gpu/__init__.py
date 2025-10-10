from typing import List

from .base import GPUBase
from .nvidia import NVIDIA
from .amd import AMD

class Driver:
    drivers: List[GPUBase] = []

    def __init__(self):
        if NVIDIA.is_support():
            self.drivers.append(NVIDIA())

        if AMD.is_support():
            self.drivers.append(AMD())

    @property
    def support(self):
        return len(self.drivers) > 0

    def get_all_device_info(self, get):
        for _driver in self.drivers:
            pass