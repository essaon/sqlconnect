from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

inlBtnAddTask = KeyboardButton(text='Добавить задание')
inlBtnDeleteTask = KeyboardButton(text='Удалить задание')
inlBtnEditTask = KeyboardButton(text='Изменить задание')
inlBtnShowTasks = KeyboardButton(text='Все задания')
inlBtnShowMyTasks = KeyboardButton(text="Мои задания")
inlBtnShowTasksThatIGiven = KeyboardButton(text="Я назначил")
adminMenu = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [inlBtnAddTask],
    [inlBtnEditTask, inlBtnDeleteTask],
    [inlBtnShowTasks, inlBtnShowMyTasks, inlBtnShowTasksThatIGiven]
])

userMenu = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[inlBtnShowTasks, inlBtnShowMyTasks]])

editMenu = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text='Название'),
                                                                KeyboardButton(text='Тип'),
                                                                KeyboardButton(text='Описание')],
                                                               [KeyboardButton(text='Дедлайн'),
                                                                KeyboardButton(text='Закрепленные люди')]],
                               one_time_keyboard=True)

notifyButtons = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
yes_button = KeyboardButton("Да", callback_data="Да")
no_button = KeyboardButton("Нет", callback_data="Нет")
notifyButtons.row(yes_button, no_button)


def make_done_button(task_id):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("Отметить как сделанное", callback_data=f"mark_done_{task_id}"))


def make_undone_button(task_id):
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("Отметить как несделанное", callback_data=f"mark_undone_{task_id}"))
