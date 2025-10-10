#!/bin/bash


CRON_FILE="/var/spool/cron/root"
BACKUP_FILE="/var/spool/cron/root_backup_$(date +%Y%m%d%H%M%S)"

# 创建crontab的备份
cp $CRON_FILE $BACKUP_FILE

# 删除以flock开头的行，并覆盖原文件
grep -vP '^\s*flock' $BACKUP_FILE > $CRON_FILE

echo "Crontab modification completed. Backup is located at $BACKUP_FILE"

