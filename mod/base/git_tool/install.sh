
if command -v apt-get &> /dev/null; then
    package_manager="apt-get"
elif command -v yum &> /dev/null; then
    package_manager="yum"
else
    echo "Git installation failed."
    exit 1
fi

# 安装Git
if [ "$package_manager" = "apt-get" ]; then
    apt-get update
    apt-get install git -y
elif [ "$package_manager" = "yum" ]; then
    yum install git -y
fi

# 验证Git安装
git_version=$(git --version)
# shellcheck disable=SC2181
if [ $? -eq 0 ]; then
    echo "Git installed successfully. Version: $git_version"
else
    echo "Git installation failed."
fi