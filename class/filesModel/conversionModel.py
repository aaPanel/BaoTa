# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <cjxin@bt.cn>
# -------------------------------------------------------------------
import json
import os
import sys
import time
import traceback

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
# 文件格式转化
# ------------------------------
from filesModel.base import filesBase
import public



class main(filesBase):
    def __init__(self):
        self.convert_type = {
            'audio': ['mp3', 'wav', 'flac'],
            'video': ['mp4', 'avi', 'mov', 'mkv'],
            'image': ['png', 'jpeg', 'jpg', 'bmp', 'tiff', 'webp'],
            'all': ['png', 'jpeg', 'jpg', 'bmp', 'tiff', 'webp', 'mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav', 'flac']
        }

    def convert_audio(self, input_file, output_file):
        try:
            # 读取输入文件
            try:
                import librosa
            except:
                os.system('btpip install librosa')
                import librosa

            audio, sr = librosa.load(input_file)
            # 将音频转换为 WAV 格式
            try:
                import soundfile as sf
            except:
                os.system('btpip install soundfile')
                import soundfile as sf
            sf.write(output_file, audio, sr)
            if os.path.exists(output_file):
                self.write_log('{};音频;从{}->{};转换成功!'.format(int(time.time()), input_file, output_file))
            else:
                self.write_log('{};音频;从{}->{};转换失败，未检测到转换后的文件!'.format(int(time.time()), input_file, output_file))
                return False
            if self.is_del:
                os.remove(input_file)
                self.write_log('{};音频;从{};已删除源文件!'.format(int(time.time()), input_file))
            return True
        except:
            print(traceback.format_exc())
            self.write_log('{};音频;从{}->{};转换失败!'.format(int(time.time()), input_file, output_file))
            if os.path.exists(output_file):
                os.remove(output_file)
            return False

    def convert_video(self, input_file, output_file):
        try:

            try:
                import imageio
            except:
                os.system('btpip install imageio')
                import imageio

            import imageio
            # 读取输入文件
            reader = imageio.get_reader(input_file)
            # 创建输出文件
            try:
                meta_data = reader.get_meta_data()
                writer = imageio.get_writer(output_file, fps=meta_data["fps"])
            except ValueError:
                os.system("btpip install imageio[ffmpeg]")
                os.system("btpip install imageio[pyav]")
                meta_data = reader.get_meta_data()
                writer = imageio.get_writer(output_file, fps=meta_data["fps"])

            # 读取每一帧并写入输出文件
            for frame in reader:
                writer.append_data(frame)

            # 关闭文件
            reader.close()
            writer.close()

            if os.path.exists(output_file):
                self.write_log('{};视频;从{}->{};转换成功!'.format(int(time.time()), input_file, output_file))
            else:
                self.write_log('{};视频;从{}->{};转换失败，未检测到转换后的文件!'.format(int(time.time()), input_file, output_file))
                print('1111')
                return False
            if self.is_del:
                os.remove(input_file)
                self.write_log('{};视频;从{};已删除源文件!'.format(int(time.time()), input_file))
            return True
        except:
            print(traceback.format_exc())
            self.write_log('{};视频;从{}->{};转换失败!'.format(int(time.time()), input_file, output_file))
            if os.path.exists(output_file):
                os.remove(output_file)
            return False

    def convert_image(self, input_file, output_file):
        try:

            try:
                import cv2
            except:
                os.system('btpip install opencv-python')
                import cv2

            if output_file.split('.')[-1] in ['ico', 'svg'] or input_file.split('.')[-1] in ['ico', 'svg']:
                from PIL import Image
                img = Image.open(input_file)
                img.save(output_file, format=input_file.split('.')[-1])
            import cv2
            img = cv2.imread(input_file)
            cv2.imwrite(output_file, img)
            if os.path.exists(output_file):
                self.write_log('{};图片;从{}->{};转换成功!'.format(int(time.time()), input_file, output_file))
            else:
                self.write_log('{};图片;从{}->{};转换失败，未检测到转换后的文件!'.format(int(time.time()), input_file, output_file))
                return False
            if self.is_del:
                os.remove(input_file)
                self.write_log('{};图片;从{};已删除源文件!'.format(int(time.time()), input_file))
            return True
        except:
            print(traceback.format_exc())
            self.write_log('{};图片;从{}->{};转换失败!'.format(int(time.time()), input_file, output_file))
            if os.path.exists(output_file):
                os.remove(output_file)
            return False

    def run(self, get):
        try:
            public.set_module_logs('conversion', 'run_conversion', 1)
            if not (hasattr(get, 'pdata') and get.pdata != '[]' and get.pdata):
                return public.returnMsg(False, '转换列表为空!')
            self.is_del = int(get.get('is_save', 0))
            pdata = json.loads(get.pdata)
            if not pdata:
                return public.returnMsg(False, '参数错误!')
            result = []
            for i in pdata:
                # 判断参数是否正确
                type = [k for k, v in self.convert_type.items() if i['input_file'].split('.')[-1] in v]
                if not type:
                    result.append({'name': i['input_file'].split('/')[-1], 'status': False})
                    self.write_log('{};{};从{}->{};转换失败，不支持的格式!'.format(int(time.time()), '未知', i['input_file'], i['output_file']))
                    continue
                if os.path.exists(i['output_file']):
                    self.write_log('{};{};从{}->{};转换失败，输出地址已存在同名文件!'.format(int(time.time()), '未知', i['input_file'], i['output_file']))
                    result.append({'name': i['input_file'].split('/')[-1] + '->' + i['output_file'].split('/')[-1], 'status': False})
                    continue
                type = type[0]
                if not i['input_file'] or not i['output_file']:
                    return public.returnMsg(False, '参数错误!')
                # 判断源文件和目标文件是否相同
                if i['input_file'] == i['output_file']:
                    return public.returnMsg(False, '源文件和目标文件不能相同!')
                # 判断源文件是否存在
                if not os.path.exists(i['input_file']):
                    return public.returnMsg(False, '源文件不存在!')
                # 音频格式转换
                if type == 'audio':
                    if i['input_file'].split('.')[-1] not in self.convert_type['audio'] or i['output_file'].split('.')[-1] not in self.convert_type['audio']:
                        return public.returnMsg(False, '不支持的格式转换!')
                    if self.convert_audio(i['input_file'], i['output_file']):
                        result.append({'name': i['input_file'].split('/')[-1] + '->' + i['output_file'].split('/')[-1], 'status': True})
                    else:
                        result.append({'name': i['input_file'].split('/')[-1] + '->' + i['output_file'].split('/')[-1], 'status': False})
                # 视频格式转换
                elif type == 'video':
                    if i['input_file'].split('.')[-1] not in self.convert_type['video'] or i['output_file'].split('.')[-1] not in self.convert_type['video']:
                        return public.returnMsg(False, '不支持的格式转换!')
                    if self.convert_video(i['input_file'], i['output_file']):
                        result.append({'name': i['input_file'].split('/')[-1] + '->' + i['output_file'].split('/')[-1], 'status': True})
                    else:
                        result.append({'name': i['input_file'].split('/')[-1] + '->' + i['output_file'].split('/')[-1], 'status': False})
                # 图片格式转换
                elif type == 'image':
                    if i['input_file'].split('.')[-1] not in self.convert_type['image'] or i['output_file'].split('.')[-1] not in self.convert_type['image']:
                        return public.returnMsg(False, '不支持的格式转换!')
                    if self.convert_image(i['input_file'], i['output_file']):
                        result.append({'name': i['input_file'].split('/')[-1] + '->' + i['output_file'].split('/')[-1], 'status': True})
                    else:
                        result.append({'name': i['input_file'].split('/')[-1] + '->' + i['output_file'].split('/')[-1], 'status': False})
            return public.returnMsg(True, result)
        except:
            return traceback.format_exc()
            return public.returnMsg(False, '转换失败!')

    def get_convert_liet(self, get=None):
        # 获取转换支持列表
        try:
            return public.returnMsg(True, self.convert_type)
        except:
            return public.returnMsg(False, '获取转换支持列表失败!')

    def write_log(self, log):
        # 写入日志
        path = '/www/server/panel/logs/convert.log'
        if not os.path.exists(path):
            public.writeFile(path, '')
        public.writeFile(path, log + '\n', 'a+')

    def get_log(self, get=None):
        try:
            # 获取日志
            p = int(get.p) if hasattr(get, 'p') else 1
            row = int(get.row) if hasattr(get, 'row') else 10
            path = '/www/server/panel/logs/convert.log'
            if not os.path.exists(path):
                return public.returnMsg(True, '无日志!')
            logs = public.readFile(path)
            logs = logs.strip().split('\n')
            logs.reverse()
            logs = [i.split(';') for i in logs]
            logs = [{'time': i[0], 'type': i[1], 'operation': i[2], 'status': i[3]} for i in logs if len(i) == 4]
            data = public.get_page(len(logs), p, row)
            data['data'] = logs[p * row - row: p * row]
            return public.returnMsg(True, data)
        except:
            return traceback.format_exc()
            return public.returnMsg(False, '获取日志失败!')
