//---------------------------
// Sqlite3
//---------------------------
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sqlite3.h>

int query(char *sql,char* db_file,char*** table_data) {
    sqlite3 *db;
    char *errmsg;
    int nrow = 0;
    int ncolumn = 0;
    int i = 0;
    int j = 0;
    int rc;
    rc = sqlite3_open(db_file, &db);
    if (rc) {
        printf("Can't open database: %s\n", sqlite3_errmsg(db));
        sqlite3_close(db);
        return 0;
    }
    rc = sqlite3_get_table(db, sql, table_data, &nrow, &ncolumn, &errmsg);
    if (rc != SQLITE_OK) {
        printf("SQL error: %s\n", errmsg);
        sqlite3_free(errmsg);
        sqlite3_close(db);
        return 0;
    }
    
    sqlite3_close(db);
    sqlite3_free(errmsg);
    errmsg = NULL;
    db = NULL;
    sqlite3_shutdown();
    return nrow;
}

int execute(char *sql,char* db_file) {
    sqlite3 *db;
    int rc;
    sqlite3_stmt *stmt = NULL; 
    sqlite3_initialize();
    rc = sqlite3_open_v2(db_file, &db, SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE, NULL);
    if (rc != SQLITE_OK) {
        sqlite3_close(db);
        return 0;
    }
    rc = sqlite3_prepare_v2(db, sql, -1, &stmt, NULL);
    if (rc == SQLITE_OK) sqlite3_step(stmt);
    sqlite3_reset(stmt);
    sqlite3_finalize(stmt);
    sqlite3_db_release_memory(db);
    sqlite3_close(db);
    sqlite3_shutdown();

    return 1;
}