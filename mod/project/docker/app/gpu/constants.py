from dataclasses import dataclass


@dataclass
class CMD:
    @dataclass
    class CTK:
        @dataclass
        class APT:
            GetGPGKey = "curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg"
            AddSourcesList = "curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list"
            APTUpdate = "sudo apt-get update"
            Install = "sudo apt-get install -y nvidia-container-toolkit"
            OneInstall = GetGPGKey + ';' + AddSourcesList + ';' + APTUpdate + ';' + Install

        @dataclass
        class YUM:
            AddRepo = "curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo"
            Install = "sudo yum install -y nvidia-container-toolkit"
            OneInstall = AddRepo + ';' + Install

        @dataclass
        class ConfigureDocker:
            Runtime = "sudo nvidia-ctk runtime configure --runtime=docker"
            Restart = "sudo systemctl restart docker"

        CheckVersion = "nvidia-ctk -v"
