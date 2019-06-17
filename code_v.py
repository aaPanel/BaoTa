#coding:utf-8
import os
import sys
import shutil
import time
from distutils.core import setup
from Cython.Build import cythonize
 
 
def get_py(base_path=os.path.abspath('.'), parent_path='', name='', excepts=(), copy_other=False, del_c=False, start_time=0.0):
    """
    获取py文件的路径
    :param base_path: 根路径
    :param parent_path: 父路径
    :param name: 文件夹名
    :param excepts: 需要排除的文件
    :param copy_other: 是否copy其他文件
    :param del_c: 是否删除c文件
    :param start_time: 程序开始时间
    :return: py文件的迭代器
    """
    full_path = os.path.join(base_path, parent_path, name)
    for fname in os.listdir(full_path):  # 列出文件夹下所有路径名称，筛选返回需要的文件名称
        ffile = os.path.join(full_path, fname)
        if os.path.isdir(ffile) and not fname.startswith('.'):
            for f in get_py(base_path, os.path.join(parent_path, name), fname, excepts, copy_other, del_c):
                yield f
        elif os.path.isfile(ffile):
            ext = os.path.splitext(fname)[1]
            if ext == ".c":
                if del_c and os.stat(ffile).st_mtime > start_time:
                    os.remove(ffile)
            elif ffile not in excepts and os.path.splitext(fname)[1] not in('.pyc', '.pyx'):  # 如果文件不在排除列表中，并且文件不是.c, .pyc, .pyx
                if os.path.splitext(fname)[1] in('.py', '.pyx') and not fname.startswith('__'):
                    yield ffile
                elif copy_other:
                    dst_dir = os.path.join(base_path, parent_path, name)
                    if not os.path.isdir(dst_dir):
                        os.makedirs(dst_dir)
                    shutil.copyfile(ffile, os.path.join(dst_dir, fname))
        else:
            pass
 
 
def build_codes(path_list):
    """
    将路径列表下的文件编译成.so文件
    :param path_list
    :return:
    """
    start_time = time.time()
    for path in path_list:
        if os.path.isdir(path):  # 如果是文件夹，将so按照原路径编到对应位置
            curr_dir = os.path.abspath(path)
            parent_path = sys.argv[1] if len(sys.argv) > 1 else ""
            setup_file = os.path.join(os.path.abspath('.'), __file__)
 
            # 获取py列表
            module_list = list(get_py(base_path=curr_dir, parent_path=parent_path, excepts=(setup_file), start_time=start_time))
            try:
                for module in module_list:
                    setup(ext_modules=cythonize(module), script_args=["build_ext", "-b", os.path.abspath(os.path.dirname(module))])
            except Exception as ex:
                print("Error: ", ex)
                exit(1)
            else:
                module_list = list(get_py(base_path=curr_dir, parent_path=parent_path, excepts=(setup_file), copy_other=False, start_time=start_time))
            module_list = list(get_py(base_path=curr_dir, parent_path=parent_path, excepts=(setup_file), del_c=True, start_time=start_time))  # 删除编译过程产生的c文件
 
        elif os.path.isfile(path):  # 如果是文件，直接编译到原位置
            try:
                setup(ext_modules=cythonize(path), script_args=["build_ext", "-b", os.path.abspath(os.path.dirname(path))])
            except Exception as ex:
                print("Error", ex)
                exit(1)
            if os.path.splitext(path)[1] == '.py':
                c_path = path.replace('.py', '.c')
                if os.path.exists(c_path) and os.stat(c_path).st_atime > start_time:
                    os.remove(c_path)
 
    if os.path.exists('./build'):  # 删除build过程产生的临时文件
        shutil.rmtree('./build')
 
    print("Complete! time:", time.time()-start_time, 's')
 
 
def delete_py(path_list):
    """
    删除给定路径下的py文件
    :param path_list: 需要删除的py文件路径列表，可以是文件夹名，也可以是文件名
    :return:
    """
    for path in path_list:
        base_path = os.path.abspath(path)
        counter = 0  # 文件删除计数器
        if os.path.isfile(base_path) and os.path.splitext(base_path)[1] == '.py':
            os.remove(base_path)
            counter += 1
            if counter == len(path_list):
                return  # 直到一个文件夹中的文件删除完退出递归
        elif os.path.isdir(base_path):
            dirs = [os.path.join(base_path, _dir) for _dir in os.listdir(base_path)]
            delete_py(dirs)


if __name__ == "__main__":
    if sys.version_info[0] == 2:
        code_path_list=["/www/server/panel/plugin/tamper_proof/tamper_proof_main.py"]
    else:
        code_path_list=["/www/server/panel/plugin/tamper_proof/tamper_proof_main.py"]
    build_codes(code_path_list)
