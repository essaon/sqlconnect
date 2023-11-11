from aiogram import Bot, Dispatcher, executor, types
import markups as mk
import config
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime, timedelta
import asyncio
import re

bot = Bot(token=config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Глобальный словарь для хранения задач
tasks = {}
users = {}
reg_users = {}
admin_ids = {404134961, 938046543}
admins_tasks = {}

task_id_counter = 0
users_waiting_for_confirmation = {}

adding_task_lock = asyncio.Lock()


def is_deadline_valid(deadline):
    # Паттерн для проверки формата "DD.MM.YYYY HH:MM"
    pattern = r'^(0[1-9]|[1-2][0-9]|3[0-1])\.(0[1-9]|1[0-2])\.(20[2-9]\d) (0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$'

    if re.match(pattern, deadline):
        return True
    else:
        return False



def format_task_info(task):
    assigned_to_list = task['assigned_to'].split(',')
    assigned_to_text = ', '.join([f'@{username.strip()}' for username in assigned_to_list])

    message_text = (f"ID: {task['task_id']}\n"
                    f"Название: {task['title']}\n"
                    f"Тип: {task['type']}\n"
                    f"Описание: {task['description']}\n"
                    f"Дедлайн: {task['deadline']}\n"
                    f"Закрепленные люди: {assigned_to_text}\n"
                    f"Кто создал: @{task['who_created']}\n"
                    f"Статус: {task['status']}\n")
    return message_text


async def send_notification(assigned_to, task_id, text):
    for user_username in assigned_to:
        for user_id, username in reg_users.items():
            if username == user_username:
                print(user_username)
                message_text = text + '\n\n' + format_task_info(tasks[task_id])
                done_button = mk.make_done_button(task_id)
                await bot.send_message(user_id, message_text, reply_markup=done_button)


@dp.message_handler(text='хуй')
async def command_start(message: types.Message):
    for user_id, username in reg_users.items():
        print(user_id, username)


async def cancel_add(message: types.Message):
    global task_id_counter
    await message.answer("Добавление задачи отменено.", reply_markup=mk.adminMenu)
    del tasks[task_id_counter]
    task_id_counter -= 1
    await dp.current_state(user=message.from_user.id).set_state(None)
    return


async def send_reminder():
    while True:
        now = datetime.now()

        # Проходим по всем заданиям
        if not any(task.get('deadline') for task in tasks.values()):
            print("В словаре нет заданий с непустыми полями deadline.")
        else:
            for task_id, task in tasks.items():
                if 'assigned_to' in task and 'deadline' in task and task['deadline']:
                    deadline = datetime.strptime(task['deadline'], "%d.%m.%Y %H:%M")
                    time_difference = deadline - now
                    if time_difference > timedelta(weeks=1):
                        weeks_to_deadline = time_difference // timedelta(weeks=1)
                        if timedelta(weeks=weeks_to_deadline) <= time_difference <= timedelta(weeks=weeks_to_deadline,
                                                                                              minutes=1):
                            await send_notification(task['assigned_to'].split(','), task_id,
                                                    f"Напоминание: Ровно столько недель осталось до дедлайна: {weeks_to_deadline}, за работу!")
                    # Вычисляем разницу во времени (timedelta)
                    elif timedelta(days=7) <= time_difference <= timedelta(days=7, minutes=1):
                        await send_notification(task['assigned_to'].split(','), task_id,
                                                "Не забывай про это задание! Дедлайн через неделю!")
                    elif timedelta(days=3) <= time_difference <= timedelta(days=3, minutes=1):
                        await send_notification(task['assigned_to'].split(','), task_id,
                                                "Пора двигать попой! Дедлайн через 3 дня!")
                    elif timedelta(days=1) <= time_difference <= timedelta(days=1, minutes=1):
                        await send_notification(task['assigned_to'].split(','), task_id,
                                                "Друг, поторопись! Дедлайн через 1 день!")
                    elif timedelta(hours=1) <= time_difference <= timedelta(hours=1, minutes=1):
                        await send_notification(task['assigned_to'].split(','), task_id,
                                                "Время совсем на исходе! Дедлайн через 1 час!")

                # Проверка каждые 59 секунд
        await asyncio.sleep(59)


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        await message.answer("Привет, админ! Выберите действие:", reply_markup=mk.adminMenu)
    else:
        await message.answer("Вы зарегистрировались как обычный пользователь.", reply_markup=mk.userMenu)

    reg_users[user_id] = message.from_user.username
    print(message.from_user.id, message.from_user.username)


@dp.message_handler(text='Добавить задание')
async def add_task(message: types.Message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        global task_id_counter
        task_id_counter += 1
        admins_tasks[user_id] = task_id_counter
        await message.answer("Введите название задачи:")
        tasks[admins_tasks[user_id]] = {'task_id': '', 'title': '', 'type': '', 'description': '', 'deadline': '',
                                        'assigned_to': '',
                                        'who_created': (message.from_user.username or 'UnknownUser'),
                                        'status': 'Не сделано❌'}
        tasks[admins_tasks[user_id]]['task_id'] = admins_tasks[user_id]
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_title")
    else:
        await message.answer("У вас нет прав для этой операции")


@dp.message_handler(state="waiting_for_title")
async def process_new_task_description(message: types.Message):
    user_id = message.from_user.id
    if message.text == '/cancel':
        await cancel_add(message)
    if admins_tasks[user_id] in tasks:
        tasks[admins_tasks[user_id]]['title'] = message.text
        await message.answer("Введите тип задачи:")
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_type")


@dp.message_handler(state="waiting_for_type")
async def process_new_task_description(message: types.Message):
    user_id = message.from_user.id
    if message.text == '/cancel':
        await cancel_add(message)
    if admins_tasks[user_id] in tasks:
        tasks[admins_tasks[user_id]]['type'] = message.text
        await message.answer("Введите описание задачи:")
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_description")


@dp.message_handler(state="waiting_for_description")
async def process_new_task_description(message: types.Message):
    user_id = message.from_user.id
    if message.text == '/cancel':
        await cancel_add(message)
    if admins_tasks[user_id] in tasks:
        tasks[admins_tasks[user_id]]['description'] = message.text
        await message.answer("Введите дедлайн задачи (в формате DD.MM.YYYY HH:MM):\nНапример 15.01.2023 14:00")
        await dp.current_state(user=message.from_user.id).set_state("waiting_for_deadline")


@dp.message_handler(state="waiting_for_deadline")
async def process_new_task_deadline(message: types.Message):
    user_id = message.from_user.id
    if message.text == '/cancel':
        await cancel_add(message)
    if admins_tasks[user_id] in tasks:
        deadline = message.text
        if is_deadline_valid(deadline):
            tasks[admins_tasks[user_id]]['deadline'] = deadline
            await message.answer("Введите закрепленных людей (через запятую):")
            await dp.current_state(user=message.from_user.id).set_state("waiting_for_assigned_to")
        else:
            await message.answer("Дедлайн введен неправильно. \
Пожалуйста, проверьте корректность данных и попробуйте снова.")


@dp.message_handler(state="waiting_for_assigned_to")
async def process_new_task_assigned_to(message: types.Message):
    if message.text == '/cancel':
        await cancel_add(message)
    user_id = message.from_user.id
    if admins_tasks[user_id] in tasks:
        tasks[admins_tasks[user_id]]['assigned_to'] = message.text.replace('@', '')

        await message.answer(f"Задача успешно добавлена с ID: {admins_tasks[user_id]}")
        task = tasks[admins_tasks[user_id]]
        message_text = format_task_info(task)
        await message.answer(message_text, reply_markup=mk.adminMenu)

        # отправка уведомления прикрепленным людям
        assigned_to = tasks[admins_tasks[user_id]]['assigned_to'].split(',')
        await send_notification(assigned_to, admins_tasks[user_id], "Тебе пришла новая тасочка, пупсик:")
        # Завершаем состояние "waiting_for_assigned_to"
        await dp.current_state(user=user_id).set_state(None)


@dp.message_handler(text='Показать все задания')
async def watch_task(message: types.Message):
    if not tasks:
        await message.answer("Список задач пуст.")
    else:
        for task_id in tasks.keys():
            task = tasks[task_id]
            message_text = format_task_info(task)
            await message.answer(message_text)


@dp.message_handler(text='Показать мои задания')
async def show_my_tasks(message: types.Message):
    user_id = message.from_user.id
    user_username = message.from_user.username

    if user_id in admin_ids:
        # Если пользователь - админ, показать задания, которые он создал
        admin_tasks = [task for task in tasks.values() if task['who_created'] == message.from_user.username]
        if admin_tasks:
            for task in admin_tasks:
                message_text = format_task_info(task)
                await message.answer(message_text)
        else:
            await message.answer("Вы еще не создали ни одной задачи.")
    else:
        # Если пользователь - обычный пользователь, показать задания, которые назначены ему
        user_assigned_tasks = [task for task in tasks.values() if user_username in task['assigned_to'].split(',')]
        if user_assigned_tasks:
            for task in user_assigned_tasks:
                message_text = format_task_info(task)
                await message.answer(message_text)
        else:
            await message.answer("Вам пока не назначены задачи.")


# Где `admin_ids` - множество, в котором перечислены идентификаторы админов


@dp.message_handler(text='Удалить задание')
async def request_task_id(message: types.Message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        if not tasks:
            await message.answer("Список задач пуст.")
        else:
            # Отправляем сообщение с просьбой ввести ID задачи
            await message.answer("Введите ID задачи для удаления:")

            # Устанавливаем состояние ожидания ввода ID задачи
            await dp.current_state(user=message.from_user.id).set_state("waiting_for_task_id")
    else:
        await message.answer("У вас нет прав для этой операции")


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
    user_id = message.from_user.id
    if user_id in admin_ids:
        if not tasks:
            await message.answer("Список задач пуст.")
        else:
            # Отправляем сообщение с просьбой ввести ID задачи
            await message.answer("Введите ID задачи для редактирования:")

            # Устанавливаем состояние ожидания ввода ID задачи
            await dp.current_state(user=message.from_user.id).set_state("waiting_for_task_id_2")
    else:
        await message.answer("У вас нет прав для этой операции")


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


@dp.message_handler(lambda message: message.text in ["Название", "Тип", "Описание", "Дедлайн", "Закрепленные люди"])
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
    if user_id in admin_ids:
        if user_id in users:
            if 'editing' in users[user_id]:
                if 'field_to_edit' in users[user_id] and 'editing_value' in users[user_id]:
                    # Пользователь отменил редактирование поля задачи
                    del users[user_id]['editing']
                    del users[user_id]['field_to_edit']
                    del users[user_id]['editing_value']
                    await message.answer("Редактирование отменено.", reply_markup=mk.adminMenu)
                    return
        else:
            await message.answer("Нет активных действий для отмены.", reply_markup=mk.adminMenu)
            return
    else:
        await message.answer("У вас нет прав", reply_markup=mk.userMenu)
        return


@dp.callback_query_handler(lambda callback: callback.data.startswith("mark_done_"))
async def handle_mark_done(callback: types.CallbackQuery):
    # Извлекаем данные из callback_query.data
    task_id = int(callback.data.split("_")[2])

    if task_id in tasks:
        # Помечаем задачу как выполненную
        tasks[task_id]['status'] = "Сделано✅"
        text_message = format_task_info(tasks[task_id])

        # Отправляем уведомление создателю задачи
        task_creator = tasks[task_id]['who_created']
        creator_id = next((user_id for user_id, user_username in reg_users.items() if user_username == task_creator), None)
        if creator_id is not None:
            await bot.send_message(creator_id, f"Пользователь @{callback.from_user.username} \
отметил вашу задачу (ID {task_id}) как выполненную.")
            await bot.send_message(creator_id, text_message)
            print(f"ID для пользователя {task_creator}: {creator_id}")
        else:
            # Идентификатор не найден
            print(f"Пользователь {task_creator} не найден.")
        await bot.edit_message_text(chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    text=text_message,
                                    reply_markup=mk.make_undone_button(task_id))
        # Отправим сообщение с уведомлением, что задание выполнено
    await callback.answer()


@dp.callback_query_handler(lambda callback: callback.data.startswith("mark_undone_"))
async def handle_mark_undone(callback: types.CallbackQuery):
    # Извлекаем данные из callback_query.data
    task_id = int(callback.data.split("_")[2])

    if task_id in tasks:
        # Помечаем задачу как невыполненную
        tasks[task_id]['status'] = "Не сделано❌"
        text_message = format_task_info(tasks[task_id])
        # Отправляем уведомление создателю задачи
        task_creator = tasks[task_id]['who_created']
        creator_id = next((user_id for user_id, user_username in reg_users.items() if user_username == task_creator), None)
        if creator_id is not None:
            await bot.send_message(creator_id, f"Пользователь @{callback.from_user.username} \
отметил вашу задачу (ID {task_id}) как невыполненную.")
            await bot.send_message(creator_id, text_message)
            print(f"ID для пользователя {task_creator}: {creator_id}")
        else:
            # Идентификатор не найден
            print(f"Пользователь {task_creator} не найден.")
        await bot.edit_message_text(chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    text=text_message,
                                    reply_markup=mk.make_done_button(task_id))
    await callback.answer()



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
        task['assigned_to'] = new_value.replace('@', '')

    # Формируем текст для сообщения с обновленными данными
    message_text = format_task_info(task)

    await message.answer(f"Поле '{field_to_edit}' отредактировано. Новое значение: {new_value}")
    await message.answer(message_text, reply_markup=mk.adminMenu)

    # Завершаем редактирование
    del users[user_id]['editing']
    del users[user_id]['field_to_edit']
    del users[user_id]['editing_value']


async def on_startup(dp):
    asyncio.create_task(send_reminder())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
