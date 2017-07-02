import sqlite3


class DBHelper:
    def __init__(self, dbname="todo.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)
        self.meetup_started = False

    def setup(self):
         todo_tblstmt = "CREATE TABLE IF NOT EXISTS items (description text, owner text)"
         meetup_tbltstmt = "CREATE TABLE IF NOT EXISTS meetup_users (userid int, name text, free_dates text)"
         itemidx = "CREATE INDEX IF NOT EXISTS itemIndex ON items (description ASC)"
         ownidx = "CREATE INDEX IF NOT EXISTS ownIndex ON items (owner ASC)"
         self.conn.execute(todo_tblstmt)
         self.conn.execute(meetup_tbltstmt)
         self.conn.execute(itemidx)
         self.conn.execute(ownidx)
         self.conn.commit()

    def add_item(self, item_text, owner):
        stmt = "INSERT INTO items (description, owner) VALUES (?, ?)"
        args = (item_text, owner)
        self.conn.execute(stmt, args)
        self.conn.commit()

    def delete_item(self, item_text, owner):
        stmt = "DELETE FROM items WHERE description = (?) AND owner = (?)"
        args = (item_text, owner )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_items(self, owner):
        stmt = "SELECT description FROM items WHERE owner = (?)"
        args = (owner, )
        return [x[0] for x in self.conn.execute(stmt, args)]

    def edit_item_text(self, item_text,new_item_text,owner):
        stmt = "UPDATE items SET description = (?) WHERE description = (?) AND owner = (?)"
        args = (new_item_text, item_text, owner )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def add_user(self, userid, username):
        stmt = "INSERT INTO meetup_users (userid,name) VALUES (?, ?)"
        args = (userid,username)
        self.conn.execute(stmt, args)
        self.conn.commit()
