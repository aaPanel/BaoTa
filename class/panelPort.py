#coding:utf-8
import socket
import threading
import time
import public

ports = []

class SkPort(threading.Thread):
    def __init__(self,ip,port):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
    def run(self):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(10)
        try:
            sk.connect((self.ip,self.port))
            tmp = {}
            tmp['port'] = self.port
            tmp['process'] = public.ExecShell("lsof -i :"+str(self.port)+"|grep -v COMMAND|awk '{print $1}'")[0].split('\n')[0].strip();
            ports.append(tmp);
        except Exception,e:
            #print e
            pass
        sk.close()
def main():
    ip = '127.0.0.1';
    sport = 1
    eport = 65535
    for port in range(sport,eport+1):
        item = (ip,port)
        t = SkPort(ip,port)
        t.start()
            
    
    print str(ports)
     
if __name__ == '__main__':
    main()