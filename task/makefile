CC=gcc
FLAG=
LARGS=-lpthread -lsqlite3
TOFILE=/www/server/panel/BT-Task

all:bt-task

bt-task:bt-task.c
	$(CC) bt-task.c $(FLAG) -o $(TOFILE) $(LARGS)

run:$(TOFILE)
	./$(TOFILE)

clean:
	rm -f $(TOFILE)