import sys
from collections import defaultdict
from functools import wraps

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')

import public

try:
    import pynvml
except:
    public.ExecShell("btpip install nvidia-ml-py")
    import pynvml

try:
    from mod.project.docker.app.gpu.base import GPUBase
except:
    class GPUBase:
        pass

device_tasks = defaultdict()
system_tasks = defaultdict()


def register_task(name: str):
    def task_decorator(task_func):
        _task_type, _task_name = name.split(':')
        if _task_type == 'device':
            device_tasks[_task_name] = task_func
        elif _task_type == 'system':
            system_tasks[_task_name] = task_func

        @wraps(task_func)
        def func_wrapper(*args, **kwargs):
            return task_func(*args, **kwargs)

        return func_wrapper

    return task_decorator


class NVIDIA(GPUBase):
    name = 'nvidia'
    support = None

    def __init__(self):
        # 判断是否支持，并在判断时初始化pynvml库。
        self.device_count = 0
        if self.is_support():
            self.device_count = pynvml.nvmlDeviceGetCount()

    def __del__(self):
        if self.is_support():
            pynvml.nvmlShutdown()

    def get_all_device_info(self):
        all_info = defaultdict()
        all_info['system'] = self.get_system_info()
        for index in range(self.device_count):
            all_info[index] = self.get_info_by_index(index)
        return all_info

    def get_info_by_index(self, index=0):
        info = defaultdict()
        handle = pynvml.nvmlDeviceGetHandleByIndex(index)

        for t_name, t_func in device_tasks.items():
            try:
                info[t_name] = t_func(self, handle)
            except:
                # public.print_log("pynvml {t_name} error: {}")
                info[t_name] = None

        return info

    def get_system_info(self):
        info = defaultdict()
        for t_name, t_func in system_tasks.items():
            try:
                info[t_name] = t_func(self)
            except:
                # public.print_log(f"pynvml {t_name} error: {e}")
                info[t_name] = None
        return info

    @classmethod
    def is_support(cls):
        try:
            pynvml.nvmlInit()
            cls.support = True
            return True

        except pynvml.NVMLError:
            cls.support = False
            # public.print_log("Nvidia was not supported!")
            return False

    @register_task('device:memory')
    def _get_mem_info(self, handle):
        info = defaultdict()
        info['size'] = int(pynvml.nvmlDeviceGetMemoryInfo(handle).total) / 1024 ** 3
        info['free'] = int(pynvml.nvmlDeviceGetMemoryInfo(handle).free) / 1024 ** 3
        info['used'] = int(pynvml.nvmlDeviceGetMemoryInfo(handle).used) / 1024 ** 3
        return info

    @register_task('device:clock')
    def _get_clock_info(self, handle):
        info = defaultdict()
        info['graphics'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
        info['sm'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
        info['memory'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
        info['video'] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_VIDEO)

        return info

    @register_task('device:temperature')
    def _get_temp_info(self, handle):
        info = 0
        try:
            info = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        except pynvml.NVMLError or AttributeError:
            info = pynvml.nvmlDeviceGetTemperatureV1(handle, pynvml.NVML_TEMPERATURE_GPU)
        return info

    @register_task('device:utilization')
    def _get_uti_info(self, handle):
        info = defaultdict()
        info['gpu'] = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
        info['memory'] = pynvml.nvmlDeviceGetUtilizationRates(handle).memory

        return info

    @register_task('device:processes')
    def _get_proc_uti(self, handle):
        info = list()
        for p in pynvml.nvmlDeviceGetComputeRunningProcesses(handle):
            p.__dict__['name'] = pynvml.nvmlSystemGetProcessName(p.pid)
            p.__dict__['type'] = 'Compute'
            info.append(p.__dict__)

        for p in pynvml.nvmlDeviceGetGraphicsRunningProcesses(handle):
            p.__dict__['name'] = pynvml.nvmlSystemGetProcessName(p.pid)
            p.__dict__['type'] = 'Graphics'
            info.append(p.__dict__)

        for p in pynvml.nvmlDeviceGetMPSComputeRunningProcesses(handle):
            p.__dict__['name'] = pynvml.nvmlSystemGetProcessName(p.pid)
            p.__dict__['type'] = 'MPS'
            info.append(p.__dict__)

        return info

    @register_task('device:fan')
    def _get_fan_info(self, handle):
        info = defaultdict()
        try:
            info['speed'] = pynvml.nvmlDeviceGetFanSpeedRPM(handle).speed
        except AttributeError:
            info['speed'] = pynvml.nvmlDeviceGetFanSpeed(handle)
        except pynvml.NVMLError:
            info['speed'] = pynvml.nvmlDeviceGetFanSpeed_v2(handle, 0)
        except:
            info['speed'] = 0
        return info

    @register_task('device:name')
    def _get_device_name(self, handle):
        return pynvml.nvmlDeviceGetName(handle)

    @register_task('device:power')
    def _get_device_power(self, handle):
        info = defaultdict()
        info['current'] = pynvml.nvmlDeviceGetPowerUsage(handle)
        info['max'] = pynvml.nvmlDeviceGetPowerManagementLimit(handle)
        return info

    @register_task('system:version')
    def _get_device_version(self):
        info = defaultdict()
        info['driver'] = pynvml.nvmlSystemGetDriverVersion()

        try:
            info['cuda'] = pynvml.nvmlSystemGetCudaDriverVersion()
        except pynvml.NVMLError or AttributeError:
            info['cuda'] = pynvml.nvmlSystemGetCudaDriverVersion_v2()

        return info

    @register_task('system:count')
    def _get_device_count(self):
        info = 0
        info = pynvml.nvmlDeviceGetCount()
        return info


if __name__ == '__main__':
    nvidia = NVIDIA()
    print(nvidia.get_all_device_info())
