#!/bin/python
#coding: utf-8
import requests,re
headers = {'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36"}
url = 'https://www.xicidaili.com/wt/'
rep = "<td>(\d+\.\d+\.\d+\.\d+)</td>\n\s+<td>(\d+)</td>"
def get_ip(num = 100):
    ip_arr = [];
    for i in range(num):
        rs = requests.get(url + str(i),headers = headers)
        tmp  = re.findall(rep,rs.text)
        for tmp1 in tmp:
            print(tmp1)
            if len(tmp1) != 2: continue
            ip_arr.append(tmp[0]+':' + tmp[1])
    ip_text = '\n'.join(ip_arr)
    return ip_text

ip_texts = get_ip(100);
f = open('e:/ip_text.txt','w+');
f.write(ip_texts);
f.close();
