from django.db import models


class User(models.Model):
    """
    This class represents a user.

    Args:
        name (str): The user's name.
        surname (str): The user's surname.
        tg_id (str): The user's Telegram ID.
        course (int): The user's course.
        group (int): The user's group.
        type (str): The user's type.
        admin (bool): A boolean indicating whether the user is an administrator.
        superadmin (bool): A boolean indicating whether the user is a super administrator.

    Attributes:
        name (str): The user's name.
        surname (str): The user's surname.
        tg_id (str): The user's Telegram ID.
        course (int): The user's course.
        group (int): The user's group.
        type (str): The user's type.
        admin (bool): A boolean indicating whether the user is an administrator.
        superadmin (bool): A boolean indicating whether the user is a super administrator.
    """
    message_id = models.IntegerField(default = None)
    name = models.TextField(default=None) 
    surname = models.TextField(default=None)
    tg_id = models.TextField(unique=True)
    course = models.IntegerField(default=None)
    group = models.IntegerField(default=None)
    type = models.TextField(default=None)
    
    def __str__(self):
        return self.name
class Admin(models.Model):
        tg_id = models.TextField(unique = True)
class SuperAdmin(models.Model):
        tg_id = models.TextField(unique = True)

class Task(models.Model):
    """
    This class represents a task.

    Args:
        id (int, optional): The task's ID. Defaults to None.
        title (str, optional): The task's title. Defaults to None.
        type (str, optional): The task's type. Defaults to None.
        description (str, optional): The task's description. Defaults to None.
        deadline (datetime.date, optional): The task's deadline. Defaults to None.
        who_created (User, optional): The user who created the task. Defaults to None.
        status (bool, optional): A boolean indicating whether the task is completed or not. Defaults to False.
        notify (bool, optional): A boolean indicating whether the user should be notified about the task. Defaults to False.

    Attributes:
        id (int): The task's ID.
        title (str): The task's title.
        type (str): The task's type.
        description (str): The task's description.
        deadline (datetime.date): The task's deadline.
        who_created (User): The user who created the task.
        status (bool): A boolean indicating whether the task is completed or not.
        notify (bool): A boolean indicating whether the user should be notified about the task.
    """

    title = models.TextField(max_length=25)
    type = models.TextField(default=None)
    description = models.TextField(max_length=255)
    deadline = models.TextField(default=None)
    who_created = models.TextField(default=None)
    status = models.BooleanField(default=False)
    notify = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class TaskUser(models.Model):
    """
    This class represents a relationship between a user and a task.
    """

    # The user's Telegram ID
    tg_id = models.TextField()

    # The task ID
    title = models.TextField(default = None)

