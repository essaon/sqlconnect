from peewee import *
from datetime import date
#Тут оформлены запросы через ORM, которую предоставляет peewee http://docs.peewee-orm.com/en/latest/peewee/quickstart.html
db = SqliteDatabase('tasks.sqlite')

class User(Model):
    id = TextField(unique=True)
    name = TextField(maxlength = 25) 
    surname = TextField(maxlength = 50)
    tg_id = TextField(maxlength = 20, unique=True)
    course = IntegerField(maxlength = 2)
    group = IntegerField(maxlength = 2)
    type = TextField()
    admin = BooleanField()
    superadmin = BooleanField()
    
    class Meta:
        database = db
class Task(Model):
    id = TextField(unique = True)
    title = TextField(maxlength = 25)
    type = TextField()
    description = TextField(maxlength = 255)
    deadline = DateField(default = date.today())
    assignet_to = TextField()
    who_created = TextField(maxlength = 20)
    status = BooleanField()
    notify = BooleanField()
        
    class Meta:
        database = db