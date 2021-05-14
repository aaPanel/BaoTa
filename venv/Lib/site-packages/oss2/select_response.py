import platform
import struct
import requests

from .compat import to_bytes
from .exceptions import RequestError
from .exceptions import SelectOperationFailed
from .exceptions import SelectOperationClientError
from .exceptions import InconsistentError
from . import utils
import logging

logger = logging.getLogger(__name__)
"""
The adapter class for Select object's response.
The response consists of frames. Each frame has the following format:

Type  |   Payload Length |  Header Checksum | Payload | Payload Checksum

|<4-->|  <--4 bytes------><---4 bytes-------><-n/a-----><--4 bytes--------->
And we have three kind of frames.
Data Frame:
Type:8388609
Payload:   Offset    |    Data
           <-8 bytes>

Continuous Frame
Type:8388612
Payload: Offset  (8-bytes)

End Frame
Type:8388613
Payload: Offset | total scanned bytes | http status code | error message
    <-- 8bytes--><-----8 bytes--------><---4 bytes-------><---variabe--->

"""
class SelectResponseAdapter(object):

    _CHUNK_SIZE = 8 * 1024
    _CONTINIOUS_FRAME_TYPE=8388612
    _DATA_FRAME_TYPE = 8388609
    _END_FRAME_TYPE = 8388613
    _META_END_FRAME_TYPE = 8388614
    _JSON_META_END_FRAME_TYPE = 8388615
    _FRAMES_FOR_PROGRESS_UPDATE = 10

    def __init__(self, response, progress_callback = None, content_length = None, enable_crc = False):
       self.response = response
       self.frame_off_set = 0
       self.frame_length = 0
       self.frame_data = b''
       self.check_sum_flag = 0
       self.file_offset = 0
       self.finished = 0
       self.raw_buffer = b''
       self.raw_buffer_offset = 0
       #self.resp_content_iter = response.__iter__()
       self.callback = progress_callback
       self.frames_since_last_progress_report = 0
       self.content_length = content_length
       self.resp_content_iter = response.__iter__()
       self.enable_crc = enable_crc
       self.payload = b''
       self.output_raw_data = response.headers.get("x-oss-select-output-raw", '') == "true"
       self.request_id = response.headers.get("x-oss-request-id",'')
       self.splits = 0
       self.rows = 0
       self.columns = 0

    def read(self):
        if self.finished:
            return b''
        
        content=b''
        for data in self:
            content += data
        
        return content
    
    def __iter__(self):
        return self

    def __next__(self):
        return self.next()
    
    def next(self):
        if self.output_raw_data == True:
             data = next(self.resp_content_iter) 
             if len(data) != 0:
                 return data
             else: raise StopIteration

        while self.finished == 0:
            if self.frame_off_set < self.frame_length:
                data = self.frame_data[self.frame_off_set : self.frame_length]
                self.frame_length = self.frame_off_set = 0
                return data
            else:
                self.read_next_frame()
                self.frames_since_last_progress_report += 1
                if (self.frames_since_last_progress_report >= SelectResponseAdapter._FRAMES_FOR_PROGRESS_UPDATE and self.callback is not None):
                    self.callback(self.file_offset, self.content_length)
                    self.frames_since_last_progress_report = 0
        
        raise StopIteration

    def read_raw(self, amt):
        ret = b''
        read_count = 0
        while amt > 0 and self.finished == 0:
            size = len(self.raw_buffer)
            if size == 0:
                self.raw_buffer = next(self.resp_content_iter)
                self.raw_buffer_offset = 0
                size = len(self.raw_buffer)
                if size == 0:
                    break

            if size - self.raw_buffer_offset >= amt:
                data = self.raw_buffer[self.raw_buffer_offset:self.raw_buffer_offset + amt]
                data_size = len(data)
                self.raw_buffer_offset += data_size
                ret += data
                read_count += data_size
                amt -= data_size
            else:
                data = self.raw_buffer[self.raw_buffer_offset:]
                data_len = len(data)
                ret += data
                read_count += data_len
                amt -= data_len 
                self.raw_buffer = b''
        
        return ret

    def read_next_frame(self):
        frame_type = bytearray(self.read_raw(4))
        payload_length = bytearray(self.read_raw(4))
        utils.change_endianness_if_needed(payload_length) # convert to little endian
        payload_length_val = struct.unpack("I", bytes(payload_length))[0]
        header_checksum = bytearray(self.read_raw(4))

        frame_type[0] = 0 #mask the version bit
        utils.change_endianness_if_needed(frame_type) # convert to little endian
        frame_type_val = struct.unpack("I", bytes(frame_type))[0]
        if (frame_type_val != SelectResponseAdapter._DATA_FRAME_TYPE and
            frame_type_val != SelectResponseAdapter._CONTINIOUS_FRAME_TYPE and
            frame_type_val != SelectResponseAdapter._END_FRAME_TYPE and
            frame_type_val != SelectResponseAdapter._META_END_FRAME_TYPE and
            frame_type_val != SelectResponseAdapter._JSON_META_END_FRAME_TYPE):
                logger.warning("Unexpected frame type: {0}. RequestId:{1}. This could be due to the old version of client.".format(frame_type_val, self.request_id))
                raise SelectOperationClientError(self.request_id, "Unexpected frame type:" + str(frame_type_val))

        self.payload = self.read_raw(payload_length_val)
        file_offset_bytes = bytearray(self.payload[0:8])
        utils.change_endianness_if_needed(file_offset_bytes)
        self.file_offset = struct.unpack("Q", bytes(file_offset_bytes))[0]
        if frame_type_val == SelectResponseAdapter._DATA_FRAME_TYPE:
            self.frame_length = payload_length_val - 8
            self.frame_off_set = 0
            self.check_sum_flag=1
            self.frame_data = self.payload[8:]
            checksum = bytearray(self.read_raw(4))  #read checksum crc32
            utils.change_endianness_if_needed(checksum)
            checksum_val = struct.unpack("I", bytes(checksum))[0]
            if self.enable_crc:
                crc32 = utils.Crc32()
                crc32.update(self.payload)
                checksum_calc = crc32.crc
                if checksum_val != checksum_calc:
                    logger.warning("Incorrect checksum: Actual {0} and calculated {1}. RequestId:{2}".format(checksum_val, checksum_calc, self.request_id))
                    raise InconsistentError("Incorrect checksum: Actual" + str(checksum_val) + ". Calculated:" + str(checksum_calc), self.request_id)
            
        elif frame_type_val == SelectResponseAdapter._CONTINIOUS_FRAME_TYPE:
            self.frame_length = self.frame_off_set = 0
            self.check_sum_flag=1
            self.read_raw(4)
        elif frame_type_val == SelectResponseAdapter._END_FRAME_TYPE:
            self.frame_off_set = 0
            scanned_size_bytes = bytearray(self.payload[8:16])
            status_bytes = bytearray(self.payload[16:20])
            utils.change_endianness_if_needed(status_bytes)
            status = struct.unpack("I", bytes(status_bytes))[0]
            error_msg_size = payload_length_val - 20
            error_msg=b''
            error_code = b''
            if error_msg_size > 0:
                error_msg = self.payload[20:error_msg_size + 20]
                error_code_index = error_msg.find(b'.')
                if error_code_index >= 0 and error_code_index < error_msg_size - 1:
                    error_code = error_msg[0:error_code_index]
                    error_msg = error_msg[error_code_index + 1:]

            if status // 100 != 2:
                raise SelectOperationFailed(status, error_code, error_msg)
            self.frame_length = 0
            if self.callback is not None:
                self.callback(self.file_offset, self.content_length)
            self.read_raw(4) # read the payload checksum
            self.frame_length = 0
            self.finished = 1
        elif frame_type_val == SelectResponseAdapter._META_END_FRAME_TYPE or frame_type_val == SelectResponseAdapter._JSON_META_END_FRAME_TYPE:
            self.frame_off_set = 0
            scanned_size_bytes = bytearray(self.payload[8:16])
            status_bytes = bytearray(self.payload[16:20])
            utils.change_endianness_if_needed(status_bytes)
            status = struct.unpack("I", bytes(status_bytes))[0]
            splits_bytes = bytearray(self.payload[20:24])
            utils.change_endianness_if_needed(splits_bytes)
            self.splits = struct.unpack("I", bytes(splits_bytes))[0]
            lines_bytes = bytearray(self.payload[24:32])
            utils.change_endianness_if_needed(lines_bytes)
            self.rows =  struct.unpack("Q", bytes(lines_bytes))[0]

            error_index = 36
            if frame_type_val == SelectResponseAdapter._META_END_FRAME_TYPE:
                column_bytes = bytearray(self.payload[32:36])
                utils.change_endianness_if_needed(column_bytes)
                self.columns = struct.unpack("I", bytes(column_bytes))[0]
            else:
                error_index = 32
            
            error_size = payload_length_val - error_index
            error_msg = b''
            error_code = b''
            if (error_size > 0):
                error_msg = self.payload[error_index:error_index + error_size]
                error_code_index = error_msg.find(b'.')
                if error_code_index >= 0 and error_code_index < error_size - 1:
                    error_code = error_msg[0:error_code_index]
                    error_msg = error_msg[error_code_index + 1:]

            self.read_raw(4) # read the payload checksum
            self.final_status = status
            self.frame_length = 0
            self.finished = 1
            if (status / 100 != 2):
                raise SelectOperationFailed(status, error_code, error_msg)

