execfile=/www/server/panel/BT-Task
gcc bt-task.c -g -o $execfile -lpthread -lsqlite3
$execfile
# valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes $execfile