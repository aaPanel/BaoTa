#!/usr/bin/env python
#coding:utf-8
import os, sys, socket, struct, select, time

def checksum(source_string):
    sum = 0
    countTo = (len(source_string)/2)*2
    count = 0
    while count<countTo:
        thisVal = ord(source_string[count + 1])*256 + ord(source_string[count])
        sum = sum + thisVal
        sum = sum & 0xffffffff
        count = count + 2
    if countTo<len(source_string):
        sum = sum + ord(source_string[len(source_string) - 1])
        sum = sum & 0xffffffff
    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receive_one_ping(my_socket, ID, timeout):
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([my_socket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: return
        timeReceived = time.time()
        recPacket, addr = my_socket.recvfrom(1024)
        icmpHeader = recPacket[20:28]
        type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)
        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0: return

def send_one_ping(my_socket, dest_addr, ID):
    dest_addr = socket.gethostbyname(dest_addr)
    my_checksum = 0
    ICMP_ECHO_REQUEST = 8
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1) #压包
    bytesInDouble = struct.calcsize("d")
    data = (192 - bytesInDouble) * "Q"
    data = struct.pack("d", time.time()) + data
    my_checksum = checksum(header + data)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1)
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1)) # Don't know about the 1

def do_one(dest_addr, timeout):
    icmp = socket.getprotobyname("icmp")
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error, (errno, msg):
        if errno == 1:
            msg = msg + (
            " - Note that ICMP messages can only be sent from processes"
            " running as root."
          )
            raise socket.error(msg)
        raise # raise the original error
    
    my_ID = os.getpid() & 0xFFFF
    send_one_ping(my_socket, dest_addr, my_ID)
    delay = receive_one_ping(my_socket, my_ID, timeout)
    my_socket.close()
    return delay

def get_ping(timeout = 0.5):
    try:
        delay = do_one(dest_addr, timeout)
    except socket.gaierror, e:
        return -2
    
    if delay == None:
        return -1
    else:
        delay = delay * 1000
        return delay

if __name__ == '__main__':
    print verbose_ping(sys.argv[1],2)