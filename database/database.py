import sqlite3
from .task import Task
from .user import User


class SQLITE():
    
    def __init__ (self,):
        self.conn = sqlite3.connect('tasks.db')
        self.c = self.conn.cursor()
        self.c.execute('CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT, surname TEXT, tg_id TEXT, course INTEGER, group INTEGER, type TEXT, admin INTEGER, super_admin INTEGER,)')
        self.c.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, title TEXT, type TEXT, description TEXT, deadline TEXT, assignet_to TEXT, who_created TEXT, status INTEGER, notify INTEGER)')
    
    def if_admin(self, id):
        self.cursor.execute("SELECT user FROM users WHERE id = ?", (id))
        result = self.cursor.fetchone()
        if result.admin != 0:
            return True
        return False
    
    def if_super_admin(self, id):
        self.cursor.execute("SELECT user FROM users WHERE id = ?", (id))
        result = self.cursor.fetchone()
        if result.super_admin != 0:
            return True
        return False
    
    def is_deadline(self, task_id):
        self.cursor.execute('SELECT deadline FROM tasks WHERE id = ?', (task_id))
        result = self.cursor.fetchone()
        return result
    
    def get_user(self, id):
        self.cursor.execute("SELECT * FROM users WHERE id = ?", (id))
        result = self.cursor.fetchone()
        return result
    
    def create_user(self, user: User):
        self.cursor.execute('INSERT INTO users (name, surname, tg_id, course, group, type, admin) VALUES(?, ?, ?, ?, ?, ?)', (user.name, user.surname, user.tg_id, user.course, user.group, user.type, user.admin))
        self.conn.commit()
    
    def update_user_name(self, id, name):
        self.cursor.execute('UPDATE users SET name = ? WHERE id = ?', (name, id))
        self.conn.commit()
        
    def update_user_surname(self, id, surname):
        self.cursor.execute('UPDATE users SET surname =? WHERE id =?', (surname, id))
        self.conn.commit()
    
    def remove_user(self, tg_id):
        self.cursor.execute('DELETE FROM users WHERE tg_id = ?', (tg_id))
        self.conn.commit()
        
    def add_task(self, task: Task):
        self.cursor.execute('INSERT INTO tasks (name, type, description, deadline, persons, creator_id, completed, notify) VALUES(?,?,?,?,?,?,?,?)', (task.name, task.type, task.description, task.deadline, task.persons, task.creator_id, task.completed, task.notify))
        self.conn.commit()
        
    def remove_task(self, task_id):
        self.cursor.execute('DELETE FROM tasks WHERE id =?', (task_id))
        self.conn.commit()
    
    def update_task(self, task_id, field, value):
        self.cursor.execute('UPDATE tasks SET ? = ? WHERE task_id = ?', (field, value, task_id))
        
    def get_task(self, task_id):
        self.cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id))
        result = self.cursor.fetchone()
        return result

    def get_tasks_for_user(self, user_id):
        self.curser.execute("SELECT * FROM tasks WHERE id LIKE '%?%'", (user_id))
        result = self.cursor.fetchone()
        return result
    def __del__(self):
        self.conn.close()