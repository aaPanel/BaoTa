import sqlite3
import json
import sys

def get_database_json():
    # 读取databases.json的内容
    db_json_path = '/www/server/panel/config/databases.json'
    with open(db_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_table_if_not_exists(db_obj, table_name, create_table_sql):
    # 尝试创建表，如果表不存在
    try:
        db_obj.execute(create_table_sql)
        db_obj.commit()
        print(f"【创建表】'{table_name}' 已成功创建。")
    except sqlite3.OperationalError as e:
        print(f"创建表时出错：{e}")

def check_and_add_missing_fields(db_obj, table_name, field_definitions):
    cursor = db_obj.cursor()
    # 检查现有字段
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1]: row for row in cursor.fetchall()}
    
    for field_def in field_definitions:
        if isinstance(field_def, list) and len(field_def) > 2:
            field_name, field_type = field_def[1], field_def[2]
            if field_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {field_name} {field_type}")
                    db_obj.commit()
                    print(f"【添加字段】表 '{table_name}' 中缺少字段 '{field_name}'，已成功添加。")
                except sqlite3.OperationalError as e:
                    print(f"【错误】尝试向表 '{table_name}' 添加字段 '{field_name}' 时出错: {e}")

def update_database_for_table(db_name, table_name):
    db_json = get_database_json()
    db_dir = '/www/server/panel/data/db'
    db_path = f"{db_dir}/{db_name}"
    print(f"【处理数据库】正在处理数据库文件：{db_name}")
    db_obj = sqlite3.connect(db_path)

    if table_name in db_json.get(db_name, {}):
        table_info = db_json[db_name][table_name]
        print(f"【处理表】正在处理表：{table_name}")
        create_table_if_not_exists(db_obj, table_name, table_info['sql'])
        check_and_add_missing_fields(db_obj, table_name, table_info['fields'])
    else:
        print(f"表 '{table_name}' 在数据库 '{db_name}' 的定义中未找到。")

    db_obj.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <database_name> <table_name>")
        sys.exit(1)
    
    database_name = sys.argv[1]
    table_name = sys.argv[2]
    update_database_for_table(database_name, table_name)

