import os
from .util import read_file, write_file


def rsync_compatible():
    files = [
        "/www/server/panel/class/push/rsync_push.py",
        "/www/server/panel/plugin/rsync/rsync_push.py",
    ]
    for f in files:
        if not os.path.exists(f):
            continue
        src_data = read_file(f)
        if src_data.find("push_rsync_by_task_name") != -1:
            continue
        src_data = src_data.replace("""if __name__ == "__main__":
    rsync_push().main()""", """
if __name__ == "__main__":
    try:
        sys.path.insert(0, "/www/server/panel")
        from mod.base.push_mod.rsync_push import push_rsync_by_task_name
        push_rsync_by_task_name(sys.argv[1])
    except:
        rsync_push().main()
""")
        write_file(f, src_data)
