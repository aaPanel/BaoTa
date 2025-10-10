import os, sys

os.chdir('/www/server/panel')
sys.path.append('class/')
import public

ftp_backup_path = public.get_backup_path() + '/pure-ftpd/'
ftp_log_file = '/var/log/pure-ftpd.log'
if not os.path.exists(ftp_backup_path):
    public.ExecShell('mkdir -p {}'.format(ftp_backup_path))

from datetime import date, timedelta

yesterday = (date.today() + timedelta(days=-1)).strftime("%Y-%m-%d")
ftp_file = ftp_backup_path + yesterday + '_pure-ftpd.log'
conf = ''
if os.path.isfile(ftp_file):
    old_conf = public.readFile(ftp_file)
    conf += old_conf
conf += '\n'
new_conf = public.readFile(ftp_log_file)
if new_conf: conf += new_conf
public.writeFile(ftp_file, conf)
public.writeFile(ftp_log_file, '')
print('|pure-ftpd日志已切割')
