import typing


# 创建一个管道函数
def make_pipe(fs: typing.List[callable]) -> callable:
    """
        创建一个管道函数
        @param fs: callable 数据过滤函数
        @return: any
    """
    def helper(val: any) -> any:
        return my_pipe(val, fs)
    return helper


def my_pipe(val: any, fs: typing.List[callable]) -> any:
    """
        管道数据过滤函数
        @param val: any
        @param fs: callable 数据过滤函数
        @return: any
    """
    from functools import reduce
    return reduce(lambda x, y: y(x), fs, val)


def is_number(s) -> bool:
    """
        @name 判断输入参数是否一个数字
        @author Zhj<2022-07-18>
        @param  s<string|integer|float> 输入参数
        @return bool
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False
