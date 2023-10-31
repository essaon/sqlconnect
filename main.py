from aiogram import Bot, Dispatcher, executor, types
import markups as mk
from aiogram.types import CallbackQuery
import config
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import time
from datetime import datetime
import asyncio
import re

bot = Bot(token=config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Глобальный словарь для хранения задач
tasks = {}
users = {}
task_id_counter = 1
users_waiting_for_confirmation = {}

# time_ = datetime(datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute)


def is_deadline_valid(deadline):
    # Паттерн для проверки формата "DD.MM.YYYY HH:MM"
    pattern = r'^(0[1-9]|[1-2][0-9]|3[0-1]).(0[1-9]|1[0-2]).(20[2-9]\d) (0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$'

    if re.match(pattern, deadline):
        return True
    else:
        return False


def format_task_info(task):
    message_text = (f"ID: {task['task_id']}\n"
                    f"Название: {task['title']}\n"
                    f"Тип: {task['type']}\n"
                    f"Описание: {task['description']}\n"
                    f"Дедлайн: {task['deadline']}\n"
                    f"Закрепленные люди: {task['assigned_to']}\n"
                    f"Кто создал: {task['who_created']}\n"
                    f"Нужно ли присылать уведомления: {task['notify']}\n\n")
    return message_text


async def send_notification(assigned_to, task_id):
    for user_username in assigned_to:
        print(user_username)
        user = await bot.get_chat(user_username)
        print(user_username, user)
        message_text = f"Для тебя новая задача, пупсик:\n{format_task_info(tasks[task_id])}"
        await bot.send_message(user.id, message_text)


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    await message.answer("Привет! Я бот для управления задачами. Выберите действие:", reply_markup=mk.adminMenu)
    while True:
        #/await asyncio.sleep(3600)
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        if current_time == '14:23':
            await bot.send_message(message.chat.id, f'"Это сообщение отправлено в {current_time}"')
        await asyncio.sleep(60)


@dp.message_handler(text='Добавить задание')
async def add_task(message: types.Message):
    await message.answer("Введите название задачи:")
    tasks[task_id_counter] = {'task_id': '', 'title': '', 'type': '', 'description': '', 'deadline': '',
                              'assigned_to': '', 'who_created':"@" + message.from_user.username, 'notify': ''}
    tasks[task_id_counter]['task_id'] = task_id_counter
    await dp.current_state(user=message.from_user.id).set_state("waiting_for_title")


@dp.message_handler(state="waiting_for_title")
async def process_new_task_description(message: types.Message):
    if task_id_counter in tasks:
        tasks[task_id_counter]['title'] = message.text
        await message.answer("Введите тип задачи:")
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_type")


@dp.message_handler(state="waiting_for_type")
async def process_new_task_description(message: types.Message):
    if task_id_counter in tasks:
        tasks[task_id_counter]['type'] = message.text
        await message.answer("Введите описание задачи:")
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_description")


@dp.message_handler(state="waiting_for_description")
async def process_new_task_description(message: types.Message):
    if task_id_counter in tasks:
        tasks[task_id_counter]['description'] = message.text
        await message.answer("Введите дедлайн задачи (в формате DD.MM.YYYY HH:MM):\nНапример 15.01.2023 14:00")
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_deadline")


@dp.message_handler(state="waiting_for_deadline")
async def process_new_task_deadline(message: types.Message):
    global task_id_counter
    if task_id_counter in tasks:
        deadline = message.text
        if is_deadline_valid(deadline):
            tasks[task_id_counter]['deadline'] = deadline
            await message.answer("Введите закрепленных людей (через запятую):")
            await dp.current_state(user=message.from_user.id).set_state("waiting_for_assigned_to")
        else:
            await message.answer("Дедлайн введен неправильно. \
Пожалуйста, проверьте корректность данных и попробуйте снова.")


@dp.message_handler(state="waiting_for_assigned_to")
async def process_new_task_assigned_to(message: types.Message):
    if task_id_counter in tasks:
        tasks[task_id_counter]['assigned_to'] = message.text
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_notify")
        await message.answer("Выберите нужно ли присылать уведомления:", reply_markup=mk.notifyButtons)


@dp.message_handler(lambda message: message.text in ["Да", "Нет"], state="waiting_for_notify")
async def process_notify_response(message: types.Message):
    global task_id_counter
    user_id = message.from_user.id

    # Если пользователь выбрал "Да", устанавливаем notify в True, иначе в False
    tasks[task_id_counter]['notify'] = message.text

    await message.answer(f"Задача успешно добавлена с ID: {task_id_counter}")
    task = tasks[task_id_counter]
    message_text = format_task_info(task)
    await message.answer(message_text, reply_markup=mk.adminMenu)

    # отправка уведомления прикрепленным людям
    assigned_to = tasks[task_id_counter]['assigned_to'].split(',')
    # await send_notification(assigned_to, task_id_counter)
    # Завершаем состояние "waiting_for_notify_response"
    task_id_counter += 1
    await dp.current_state(user=user_id).set_state(None)


@dp.message_handler(text='Показать задания')
async def watch_task(message: types.Message):
    if not tasks:
        await message.answer("Список задач пуст.")
    else:
        for task_id in tasks.keys():
            task = tasks[task_id]
            message_text = format_task_info(task)
            await message.answer(message_text)


@dp.message_handler(text='Удалить задание')
async def request_task_id(message: types.Message):
    if not tasks:
        await message.answer("Список задач пуст.")
    else:
        # Отправляем сообщение с просьбой ввести ID задачи
        await message.answer("Введите ID задачи для удаления:")

        # Устанавливаем состояние ожидания ввода ID задачи
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_task_id")


@dp.message_handler(lambda message: message.text.isdigit(), state="waiting_for_task_id")
async def confirm_delete_task(message: types.Message):
    task_id = int(message.text)
    if task_id in tasks:
        task = tasks[task_id]
        message_text = format_task_info(task)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("Да", "Нет")
        await message.answer(f"Вы уверены, что хотите удалить следующую задачу?\n{message_text}", reply_markup=markup)

        # Устанавливаем "ожидание подтверждения удаления" в пользовательском словаре
        users_waiting_for_confirmation[message.from_user.id] = task_id
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_confirmation")
    else:
        await message.answer(f"Задачи с ID {task_id} не существует.")
        # Сбрасываем состояние ожидания
        users_waiting_for_confirmation[message.from_user.id] = None
        await dp.current_state(user=message.from_user.id).set_state(None)


@dp.message_handler(lambda message: message.text in ["Да", "Нет"], state="waiting_for_confirmation")
async def process_delete_confirmation(message: types.Message):
    user_id = message.from_user.id
    task_id = users_waiting_for_confirmation.get(user_id)

    if task_id is not None:
        if message.text == "Да":
            del tasks[task_id]
            await message.answer(f"Задача с ID {task_id} удалена.", reply_markup=mk.adminMenu)
        elif message.text == "Нет":
            await message.answer("Удаление отменено.", reply_markup=mk.adminMenu)

        # Сбрасываем состояние ожидания в пользовательском словаре
        users_waiting_for_confirmation[user_id] = None
    await dp.current_state(user=message.from_user.id).set_state(None)


@dp.message_handler(text='Изменить задание')
async def request_task_id(message: types.Message):
    if not tasks:
        await message.answer("Список задач пуст.")
    else:
    # Отправляем сообщение с просьбой ввести ID задачи
        await message.answer("Введите ID задачи для редактирования:")

        # Устанавливаем состояние ожидания ввода ID задачи
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_task_id_2")


@dp.message_handler(lambda message: message.text.isdigit(), state="waiting_for_task_id_2")
async def edit_task(message: types.Message):
    # Получаем введенный пользователем ID задачи и преобразуем его в целое число
    task_id = int(message.text)

    if task_id not in tasks:
        await message.answer(f"Задачи с ID {task_id} не существует.")
    else:
        await message.answer("Выберите, какое поле вы хотите отредактировать:", reply_markup=mk.editMenu)

        # Устанавливаем состояние редактирования задачи и передаем ID задачи и поле для редактирования
        users[message.from_user.id] = {'task_id': task_id}
        users[message.from_user.id]['editing'] = True
    await dp.current_state(user=message.from_user.id).set_state(None)


@dp.message_handler(lambda message: message.text in ["Название", "Тип", "Описание", "Дедлайн", "Закрепленные люди",
                                                     "Кто создал", "Нужно ли присылать уведомления"])
async def edit_task_field(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users or 'editing' not in users[user_id]:
        await message.answer("Неверная команда для редактирования.")
        return

    field_to_edit = message.text
    users[user_id]['field_to_edit'] = field_to_edit
    await message.answer(f"Введите новое значение для '{field_to_edit}':")
    users[user_id]['editing_value'] = True


@dp.message_handler(commands=['cancel'])
async def cancel_action(message: types.Message):
    user_id = message.from_user.id
    if user_id in tasks:
        if 'editing' in tasks[user_id]:
            if 'field_to_edit' in tasks[user_id] and 'editing_value' in tasks[user_id]:
                # Пользователь отменил редактирование поля задачи
                del tasks[user_id]['editing']
                del tasks[user_id]['field_to_edit']
                del tasks[user_id]['editing_value']
                await message.answer("Редактирование отменено.", reply_markup=mk.adminMenu)
                return
            else:
                # Пользователь отменил добавление задачи
                del tasks[user_id]
                await message.answer("Редактирование отменено.", reply_markup= mk.adminMenu)
                return
        # Другие действия, которые можно отменить
        # Добавьте их обработку здесь
    await message.answer("Действие отменено.", reply_markup= mk.adminMenu)


@dp.message_handler()
async def edit_task_field_value(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users or 'editing' not in users[user_id] or not users[user_id]['editing_value']:
        return

    field_to_edit = users[user_id]['field_to_edit']
    task_id = users[user_id]['task_id']
    new_value = message.text

    if task_id not in tasks:
        await message.answer("Задачи с таким ID не существует.")
        return

    # Редактируем поле задачи в зависимости от выбранного поля
    task = tasks[task_id]

    if field_to_edit == "Название":
        task['title'] = new_value
    elif field_to_edit == "Тип":
        task['type'] = new_value
    elif field_to_edit == "Описание":
        task['description'] = new_value
    elif field_to_edit == "Дедлайн":
        if is_deadline_valid(new_value):
            task['deadline'] = new_value
        else:
            await message.answer("Неверный формат дедлайна. Используйте формат 'DD.MM.YYYY HH:MM'.")
            return
    elif field_to_edit == "Закрепленные люди":
        task['assigned_to'] = new_value
    elif field_to_edit == "Кто создал":
        task['who_created'] = new_value
    elif field_to_edit == "Нужно ли присылать уведомления":
        task['notify'] = new_value

    # Формируем текст для сообщения с обновленными данными
    message_text = format_task_info(task)

    await message.answer(f"Поле '{field_to_edit}' отредактировано. Новое значение: {new_value}")
    await message.answer(message_text, reply_markup=mk.adminMenu)

    # Завершаем редактирование
    del users[user_id]['editing']
    del users[user_id]['field_to_edit']
    del users[user_id]['editing_value']


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
