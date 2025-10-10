from mod.project.docker.app.gpu.base import GPUBase

class AMD(GPUBase):
    @classmethod
    def is_support(cls):
        pass

    def _get_device_version(self, *args, **kwargs):
        pass

    def _get_device_name(self, *args, **kwargs):
        pass

    def _get_fan_info(self, *args, **kwargs):
        pass

    def main(self):
        pass

    def get_info(self, gpu_id=0):
        pass

    def _get_mem_info(self):
        pass

    def _get_clock_info(self):
        pass

    def _get_temp_info(self):
        pass

    def _get_uti_info(self):
        pass

    def _get_proc_uti(self, proc_name='', proc_pid=0):
        pass
