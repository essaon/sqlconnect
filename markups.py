from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
inlBtnAddTask = KeyboardButton(text='Добавить задание', callback_data='Добавить задание')
inlBtnDeleteTask = KeyboardButton(text='Удалить задание')
inlBtnEditTask = KeyboardButton(text='Изменить задание')
inlBtnShowTasks = KeyboardButton(text='Показать задания')
adminMenu = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [inlBtnAddTask, inlBtnEditTask, inlBtnDeleteTask,],
    [inlBtnShowTasks]
])


editMenu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=3)
fields = ["Название", "Тип", "Описание", "Дедлайн", "Закрепленные люди", "Кто создал",
                  "Нужно ли присылать уведомления"]

for field in fields:
    editMenu.add(field)


notifyButtons = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
yes_button = KeyboardButton("Да", callback_data="Да")
no_button = KeyboardButton("Нет", callback_data="Нет")
notifyButtons.row(yes_button, no_button)