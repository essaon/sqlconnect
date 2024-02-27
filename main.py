from aiogram import Bot, Dispatcher, executor, types
import markups as mk
import config
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from datetime import datetime, timedelta
import asyncio
import re
from web.users.models import User, Task, TaskUser, Admin, SuperAdmin
        

    

bot = Bot(token=config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Глобальный словарь для хранения задач
tasks = {} # sql
reg_users = {} # sql

admin_ids = User.objects.tg_id # sql это просто словарь с id админов
super_admin_ids = User.objects.tg_id # sql это тоже словарь с id админов, только админов покруче
# я их просто закинул в конфиг, поэтому на гите нету

users = {}
admins_tasks = {}

task_id_counter = 0
users_waiting_for_confirmation = {}

commands = {"/start", "/help", "/cancel"}

def assignet(task_id):
    Objects = TaskUser.objects.raw("SELECT tg_id FROM users_taskuser WHERE task_id =  ?", (task_id,))
    return Objects


def is_deadline_valid(deadline):
    # Паттерн для проверки формата "DD.MM.YYYY HH:MM"
    pattern = r'^(0[1-9]|[1-2][0-9]|3[0-1])\.(0[1-9]|1[0-2])\.(20[2-9]\d) (0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$'

    if re.match(pattern, deadline):
        return True
    else:
        return False


def format_task_info(task):
    assigned_to_list = TaskUser.objects.raw("SELECT tg_id FROM users_taskuser WHERE task_id = ?", (task))
    assigned_to_text = ', '.join([f'@{username.strip()}' for username in assigned_to_list])
    tasks = Task.objects.filter(title = task)

    message_text = (
        f"<b>ID:</b> {tasks.id}\n\n"
        f"<b>Название:</b> {tasks.title}\n\n"
        f"<b>Тип:</b> {tasks.type}\n\n"
        f"<b>Описание:</b> {tasks.description}\n\n"
        f"<b>Дедлайн:</b> {tasks.deadline}\n\n"
        f"<b>Закрепленные люди:</b> {assigned_to_text}\n\n"
        f"<b>Кто создал:</b> @{tasks.who_created}\n\n"
        f"<b>Статус:</b> {tasks.status}\n\n"
    )
    return message_text


async def send_notification(assigned_to, task_id, text):
    for user_username in assigned_to:
        for user_id, username in reg_users.items():
            if username == user_username:
                print(user_username)
                message_text = text + '\n\n' + format_task_info(Task.select().where(Task.id == task_id)).get()
                done_button = mk.make_done_button(task_id)
                await bot.send_message(user_id, message_text, reply_markup=done_button, parse_mode='HTML')


@dp.message_handler(text='хуй')
async def command_start(message: types.Message):
    for data in User.objects.all():
        print(f"@{data.tg_id}", data.name)
@dp.message_handler(text='penis')
async def talking(message: types.Message):
    await message.answer("Penis Talking Ultimate")

async def cancel_add(message: types.Message):
    global task_id_counter
    await message.answer("Добавление задачи отменено.", reply_markup=mk.adminMenu)
    await dp.current_state(user=message.from_user.id).set_state(None)
    return

#+
async def send_reminder():
    while True:
        now = datetime.now()

        # Проходим по всем заданиям
        if not any(Task.objects.deadline() != None):
            print("В словаре нет заданий с непустыми полями deadline.")
        else:
            for task in Task.objects.all():
                if task.deadline != None:
                    deadline = datetime.strptime(task.deadline, "%d.%m.%Y %H:%M")
                    time_difference = deadline - now
                    if time_difference > timedelta(weeks=1):
                        weeks_to_deadline = time_difference // timedelta(weeks=1)
                        if timedelta(weeks=weeks_to_deadline) <= time_difference <= timedelta(weeks=weeks_to_deadline,
                                                                                              minutes=1):
                            await send_notification(assignet(task.id), task.id,
                                                    f"Напоминание: Ровно столько недель осталось до дедлайна: {weeks_to_deadline}, за работу!")
                    # Вычисляем разницу во времени (timedelta)
                    elif timedelta(days=7) <= time_difference <= timedelta(days=7, minutes=1):
                        await send_notification(assignet(task.id), task.id,
                                                "Не забывай про это задание! Дедлайн через неделю!")
                    elif timedelta(days=3) <= time_difference <= timedelta(days=3, minutes=1):
                        await send_notification(assignet(task.id), task.id,
                                                "Пора двигать попой! Дедлайн через 3 дня!")
                    elif timedelta(days=1) <= time_difference <= timedelta(days=1, minutes=1):
                        await send_notification(assignet(task.id), task.id,
                                                "Друг, поторопись! Дедлайн через 1 день!")
                    elif timedelta(hours=1) <= time_difference <= timedelta(hours=1, minutes=1):
                        await send_notification(assignet(task.id), task.id,
                                                "Время совсем на исходе! Дедлайн через 1 час!")

                # Проверка каждые 59 секунд
        await asyncio.sleep(59)

#+
@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    user_id = message.from_user.username
    if Admin.objects.get(tg_id = user_id) or SuperAdmin.objects.get(tg_id = user_id):
        await message.answer("Привет, актив👋\nЯ таскабот, который поможет тебе получать, давать и выполнять задания к \
дедлайну🧑‍💻\n\nТасочки, которые ты должен выполнить, находятся в '<b>Мои задания</b>'\nТасочки для всего актива \
расположены в '<b>Все задания</b>'\nТасочки, которые назначил ты, доступны в '<b>Я назначил</b>' (<i>только для глав \
отдела</i>👑)\n\nКстати, ты зарегистрирован как <b>админ</b>😉\n\nУдачи🍀", reply_markup=mk.adminMenu, parse_mode='HTML')
    else:
        await message.answer("Привет, актив👋\nЯ таскабот, который поможет тебе получать, давать и выполнять задания к \
дедлайну🧑‍💻\n\nТасочки, которые ты должен выполнить, находятся в '<b>Мои задания</b>'\nТасочки для всего актива \
расположены в '<b>Все задания</b>'\n\nКстати, ты успешно зарегистрирован как <b>обычный пользователь</b>😉\n\nУдачи🍀",
                             reply_markup=mk.userMenu, parse_mode='HTML')

    User.create(message_id = message.from_user.id, tg_id = message.from_user.username)
    print(message.from_user.id, message.from_user.username)


@dp.message_handler(commands=['help'])
async def command_help(message: types.Message):
    await message.answer("Help box✨\n\n\
/start - запуск бота\n\n\
/cancel - отменяет\n\
добавление или редактирование задания\n\n\
<b>Мои задания</b> - посмотреть только мои задания\n\n\
<b>Все задания</b> - посмотреть задания всего актива\n\n\
<i>Только для админа</i>\n\n\
<b>Добавить задание</b> - назначить задание другому пользователю(пользователям)\n\n\
<b>Изменить задание</b> - изменить задание, которое ты назначил другому пользователю\n\n\
<b>Удалить задание</b> - удалить задание, которое ты назначил другому пользователю\n\n\
<b>Я назначил</b> - посмотреть задания, который ты назначил другим пользователям\n\n\
/add_admin @username - добавить админа (но ты не можешь это делать хи-хи-хи-ха)\n\n\
/delete_admin @username - удалить админа (это тоже не можешь хи-хи-хи-ха)\n\n\
По всем вопросам и предложениям обращаться к @payalnik144", reply_markup=mk.adminMenu, parse_mode='HTML')

#+
@dp.message_handler(text='Добавить задание')
async def add_task(message: types.Message):
    user_id = message.from_user.username
    if Admin.objects.get(tg_id = user_id) or SuperAdmin.objects.get(tg_id = user_id):
        await message.answer("Введите название задачи:")
        author = message.from_user.username
        state = dp.current_state(user=message.from_user.id)
        await state.set_state("waiting_for_title")
        await state.update_data(author=author)  # сохраняем автора в context_data
    else:
        await message.answer("Не лееезь, у тебя нет прав для этой операции🤓")

@dp.message_handler(state="waiting_for_title")
async def process_new_task_description(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    if message.text == '/cancel':
        await cancel_add(message)
    title = message.text
    await message.answer("Введите тип задачи:")
    await state.set_state("waiting_for_type")
    await state.update_data(title = title)
#+
@dp.message_handler(state="waiting_for_type")
async def process_new_task_description(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    if message.text == '/cancel':
        await cancel_add(message)
    type = message.text
    await message.answer("Введите описание задачи:")
    await state.set_state("waiting_for_description")
    await state.update_data(type = type)

#+
@dp.message_handler(state="waiting_for_description")
async def process_new_task_description(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    if message.text == '/cancel':
        await cancel_add(message)
    description = message.text
    await message.answer("Введите дедлайн задачи (в формате DD.MM.YYYY HH:MM):\n<i>например</i>, 15.01.2023 14:00",
                             parse_mode='HTML')
    await state.set_state("waiting_for_deadline")
    await state.update_data(description = description)

#+
@dp.message_handler(state="waiting_for_deadline")
async def process_new_task_deadline(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    user_id = message.from_user.id
    if message.text == '/cancel':
        await cancel_add(message)
    if admins_tasks[user_id] in tasks:
        deadline = message.text
        if is_deadline_valid(deadline):
            await message.answer("Введите тэги закрепленных людей (через запятую):\n<i>например</i>, @mikitakiselev143, \
@mikitakiselev144, @mikitakiselev145", parse_mode='HTML')
            await state.set_state("waiting_for_assigned_to")
            await state.update_data(deadline = deadline)
        else:
            await message.answer("Дедлайн введен неправильно. \
Пожалуйста, проверьте корректность данных и попробуйте снова.")

#+
@dp.message_handler(state="waiting_for_assigned_to")
async def process_new_task_assigned_to(message: types.Message):
    state = dp.current_state(user=message.from_user.id)
    user_id = message.from_user.id
    data = await state.get_data()
    title = data.get("title")
    author = data.get("author")
    description = data.get("description")
    type = data.get("type")
    deadline = data.get("deadline")
    if message.text == '/cancel':
        await cancel_add(message)
    assigned_to = message.text.replace('@', '').replace(' ', '')
    for i in assigned_to:
        TaskUser.create(tg_id = i, title = title)
    Task.create(title = title, type = type, description = description, deadline = deadline, who_created = author)
    task_id = Task.objects.raw("SELECT id FROM users_task WHERE title = ?", (title))
    await message.answer(f"Задача успешно добавлена с ID: {task_id}")
    message_text = format_task_info(title)
    await message.answer(message_text, reply_markup=mk.adminMenu, parse_mode='HTML')

    # отправка уведомления прикрепленным людям
    await send_notification(assigned_to, task_id, "Тебе пришла новая тасочка, пупсик:")
    # Завершаем состояние "waiting_for_assigned_to"
    await dp.current_state(user=user_id.set_state(None))

#+
@dp.message_handler(text='Все задания')
async def watch_task(message: types.Message):
    if not tasks:
        await message.answer("Список задач пуст.")
    else:
        for task in Task.objects.all():
            message_text = format_task_info(task.title)
            await message.answer(message_text, parse_mode='HTML')

#+
@dp.message_handler(text='Мои задания')
async def show_my_tasks(message: types.Message):
    user_username = message.from_user.username

    user_assigned_tasks = TaskUser.objects.raw("SELECT title FROM users_taskuser WHERE tg_id = ?", (user_username,))
    if user_assigned_tasks:
        for task in user_assigned_tasks:
            task_info = Task.objects.filter(title = task)
            message_text = format_task_info(task)
            if task_info.status == 0:
                done_button = mk.make_done_button(task_info.id)
                await message.answer(message_text, reply_markup=done_button, parse_mode='HTML')
            else:
                undone_button = mk.make_undone_button(task_info.id)
                await message.answer(message_text, reply_markup=undone_button, parse_mode='HTML')
    else:
        await message.answer("Вам пока не назначены задачи.")

#+
@dp.message_handler(text='Я назначил')
async def show_tasks_given_you(message: types.Message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        user = message.from_user.username
        if Admin.objects.get(tg_id = user) or SuperAdmin.objects.get(tg_id = user):
            for task in Task.objects.filter(who_created = user):
                message_text = format_task_info(task.id)
                await message.answer(message_text, parse_mode='HTML')
        else:
            await message.answer("Вы еще не создали ни одной задачи.")

#+
@dp.message_handler(text='Удалить задание')
async def request_task_id(message: types.Message):
    user_id = message.from_user.id
    user = message.from_user.username
    if Admin.objects.get(tg_id = user_id) or SuperAdmin.objects.get(tg_id = user_id):
        if Task.objects.filter(who_created = user) == []:
            await message.answer("Список задач пуст.")
        else:
            # Отправляем сообщение с просьбой ввести ID задачи
            await message.answer("Введите ID задачи для удаления:")

            # Устанавливаем состояние ожидания ввода ID задачи
            await dp.current_state(user=message.from_user.id).set_state("waiting_for_task_id")
    else:
        await message.answer("Не лееезь, у тебя нет прав для этой операции🤓")

#+
@dp.message_handler(state="waiting_for_task_id")
async def confirm_delete_task(message: types.Message):
    if message.text in commands:
        await message.answer("Удаление отменено.", reply_markup=mk.adminMenu)
        await dp.current_state(user=message.from_user.id).set_state(None)
        return
    if not message.text.isdigit():
        await message.answer("ID задачи должен состоять только из цифр, попробуйте снова.")
        return
    task_id = int(message.text)
    if Task.objects.get(id = task_id):
        task = Task.objects.get(id = task_id)
        if task.who_created != message.from_user.username and SuperAdmin.objects.get(tg_id = message.from_user.username) == []:
            await message.answer("Вы не можете удалить задачу, которую создал другой админ.")
            await dp.current_state(user=message.from_user.id).set_state(None)
        else:
            message_text = format_task_info(task.title)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add("Да", "Нет")
            await message.answer(f"Вы уверены, что хотите удалить следующую задачу?\n{message_text}", reply_markup=markup, parse_mode='HTML')

            # Устанавливаем "ожидание подтверждения удаления" в пользовательском словаре
            users_waiting_for_confirmation[message.from_user.id] = task_id
            await dp.current_state(user=message.from_user.id).set_state("waiting_for_confirmation")
    else:
        await message.answer(f"Задачи с ID {task_id} не существует.")
        # Сбрасываем состояние ожидания
        users_waiting_for_confirmation[message.from_user.id] = None
        await dp.current_state(user=message.from_user.id).set_state(None)

#+
@dp.message_handler(state="waiting_for_confirmation")
async def process_delete_confirmation(message: types.Message):
    user_id = message.from_user.id
    task_id = users_waiting_for_confirmation.get(user_id)
    if message.text in commands:
        await message.answer("Удаление отменено.", reply_markup=mk.adminMenu)
        await dp.current_state(user=message.from_user.id).set_state(None)
        return
    if task_id is not None:
        if message.text == "Да":
            Task.objects.filter(id =task_id).delete()
            await message.answer(f"Задача с ID {task_id} удалена.", reply_markup=mk.adminMenu)
        elif message.text == "Нет":
            await message.answer("Удаление отменено.", reply_markup=mk.adminMenu)

        # Сбрасываем состояние ожидания в пользовательском словаре
        users_waiting_for_confirmation[user_id] = None
    await dp.current_state(user=message.from_user.id).set_state(None)

#+
@dp.message_handler(text='Изменить задание')
async def request_task_id(message: types.Message):
    user_id = message.from_user.username
    if Admin.objects.get(tg_id = user_id) != [] or SuperAdmin.objects.get(tg_id = user_id) != []:
        if Task.objects.get(who_created = user_id) == []:
            await message.answer("Список задач пуст.")
        else:
            # Отправляем сообщение с просьбой ввести ID задачи
            await message.answer("Введите ID задачи для редактирования:")

            # Устанавливаем состояние ожидания ввода ID задачи
            await dp.current_state(user=message.from_user.id).set_state("waiting_for_task_id_2")
    else:
        await message.answer("Не лееезь, у тебя нет прав для этой операции🤓")

#+
@dp.message_handler(state="waiting_for_task_id_2")
async def edit_task(message: types.Message):
    # Получаем введенный пользователем ID задачи и преобразуем его в целое число
    if message.text in commands:
        await message.answer("Редактирование отменено.", reply_markup=mk.adminMenu)
        await dp.current_state(user=message.from_user.id).set_state(None)
        return
    if not message.text.isdigit():
        await message.answer("ID задачи должен состоять только из цифр, попробуйте снова.")
        return
    task_id = int(message.text)

    if Task.objects.filter(id = task_id) == []:
        await message.answer(f"Задачи с ID {task_id} не существует.")
        await dp.current_state(user=message.from_user.id).set_state(None)
        return
    else:
        task = Task.objects.get(id = task_id)
        if task.who_created != message.from_user.username and SuperAdmin.objects.get(tg_id = message.from_user.username) != []:
            await message.answer("Вы не можете редактировать задачу, которую создал другой админ.")
        else:
            await message.answer("Выберите, какое поле вы хотите отредактировать:", reply_markup=mk.editMenu)

            # Устанавливаем состояние редактирования задачи и передаем ID задачи и поле для редактирования
            state = dp.current_state(user=message.from_user.id)
    await state.set_state("waiting_for_field_to_edit")
    await state.update_data(task_id = task_id)

#+
@dp.message_handler(state="waiting_for_field_to_edit")
async def edit_task_field(message: types.Message):
    user_id = message.from_user.username
    if User.objects.get(tg_id = user_id) == [] or 'editing' not in users[user_id]:
        await message.answer("Неверная команда для редактирования.")
        await dp.current_state(user=message.from_user.id).set_state(None)
        return

    if message.text in commands:
        await message.answer("Редактирование отменено.", reply_markup=mk.adminMenu)
        await dp.current_state(user=message.from_user.id).set_state(None)
        return

    if message.text not in ['Название', 'Тип', 'Описание', 'Дедлайн', 'Закрепленные люди']:
        await message.answer("Неверное название поля, попробуйте снова.")
        return

    field_to_edit = message.text
    if field_to_edit == 'Дедлайн':
        await message.answer(f"Введите новое значение для '{field_to_edit}' в формате DD.MM.YYYY HH:MM:\n<i>например</i>, \
15.01.2023 14:00", parse_mode='HTML')
    elif field_to_edit == 'Закрепленные люди':
        await message.answer(f"Введите новое значение для '{field_to_edit}' через запятую:\n<i>например</i>, \
@payalnik143, @payalnik144, @payalnik145", parse_mode='HTML')
    else:
        await message.answer(f"Введите новое значение для '{field_to_edit}':")
    state = dp.current_state(user=message.from_user.id)
    await state.set_state("waiting_for_editing_value")
    await state.update_data(field_to_edit=field_to_edit )

#+
@dp.message_handler(state="waiting_for_editing_value")
async def edit_task_field_value(message: types.Message):
    user_id = message.from_user.id
    state = dp.current_state(user=message.from_user.id)
    data = await state.get_data()
    task_id = data("task_id")
    field_to_edit = data("field_to_edit")
    if message.text in commands:
        await message.answer("Редактирование отменено.", reply_markup=mk.adminMenu)
        await dp.current_state(user=message.from_user.id).set_state(None)
        return

    new_value = message.text

    if task_id not in tasks:
        await message.answer("Задачи с таким ID не существует.")
        await dp.current_state(user=message.from_user.id).set_state(None)
        return

    # Редактируем поле задачи в зависимости от выбранного поля
    task = Task.objects.get(id = task_id)

    if field_to_edit == "Название":
        task.title = new_value
        task.save()
    elif field_to_edit == "Тип":
        task.type = new_value
        task.save()
    elif field_to_edit == "Описание":
        task.description = new_value
        task.save()
    elif field_to_edit == "Дедлайн":
        if is_deadline_valid(new_value):
            task.deadline = new_value
            task.save()
        else:
            await message.answer("Неверный формат дедлайна. Используйте формат 'DD.MM.YYYY HH:MM'.")
            return
    elif field_to_edit == "Закрепленные люди":
        users = new_value.replace('@', '').replace(' ', '').split(',')
        TaskUser.objects.filter(title =Task.objects.get(id=task_id).title).delete()
        for user in users:
            TaskUser.create(tg_id = user, title = Task.objects.get(id=task_id).title)

    # Формируем текст для сообщения с обновленными данными
    message_text = format_task_info(task.title)

    await message.answer(f"Поле '{field_to_edit}' отредактировано. Новое значение: {new_value}")
    await message.answer(message_text, reply_markup=mk.adminMenu, parse_mode='HTML')
    await send_notification(assignet(task_id), task_id, f"Админ @{message.from_user.username} \
отредактировал вашу задачу (ID: {task_id})\nДержу в курсе, бро🤙")
    await dp.current_state(user=user_id).set_state(None)

#+
@dp.callback_query_handler(lambda callback: callback.data.startswith("mark_done_"))
async def handle_mark_done(callback: types.CallbackQuery):
    # Извлекаем данные из callback_query.data
    task_id = int(callback.data.split("_")[2])
    
    if Task.objects.filter(id=task_id)!=[]:
        # Помечаем задачу как выполненную
        task = Task.objects.get(id=task_id)
        task.status = 1
        task.save()
        text_message = format_task_info(task.title)

        # Отправляем уведомление создателю задачи
        task_creator = task.who_created
        creator_id = User.objects.get(tg_id = task_creator).message_id
        if creator_id is not None:
            text_message2 = f"Пользователь @{callback.from_user.username} \
отметил вашу задачу (ID: {task_id}) как выполненную.\n\n"+text_message

            message = await bot.send_message(creator_id, text_message2, parse_mode="HTML")
            tasks[task_id]['notification_message_id'] = message.message_id
            print(f"ID для пользователя {task_creator}: {creator_id}")
        else:
            # Идентификатор не найден
            print(f"Пользователь {task_creator} не найден, возможно, не зарегистрирован.")
        await bot.edit_message_text(chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    text=text_message,
                                    reply_markup=mk.make_undone_button(task_id), parse_mode="HTML")

    await callback.answer()

#+
@dp.callback_query_handler(lambda callback: callback.data.startswith("mark_undone_"))
async def handle_mark_undone(callback: types.CallbackQuery):
    # Извлекаем данные из callback_query.data
    task_id = int(callback.data.split("_")[2])

    if Task.objects.filter(id=task_id)!=[]:
        # Помечаем задачу как невыполненную
        task = Task.objects.get(id=task_id)
        task.status = 0
        text_message = format_task_info(task.title)
        # Отправляем уведомление создателю задачи
        task_creator = task.who_created
        creator_id = User.objects.get(tg_id = task_creator).message_id
        if creator_id is not None:

            text_message2 = f"Пользователь @{callback.from_user.username} \
отметил вашу задачу (ID: {task_id}) как невыполненную.\n\n" + text_message

            message = await bot.send_message(creator_id, text_message2, parse_mode="HTML")
            tasks[task_id]['notification_message_id'] = message.message_id

            print(f"ID для пользователя {task_creator}: {creator_id}")
        else:
            # Идентификатор не найден
            print(f"Пользователь {task_creator} не найден, возможно, не зарегистрирован.")
        await bot.edit_message_text(chat_id=callback.from_user.id,
                                    message_id=callback.message.message_id,
                                    text=text_message,
                                    reply_markup=mk.make_done_button(task_id), parse_mode="HTML")
    await callback.answer()

#+
@dp.message_handler(lambda message: message.text.startswith("/add_admin"))
async def handle_add_admin(message: types.Message):
    user_id = message.from_user.username
    if Admin.objects.get(tg_id = user_id) == [] and SuperAdmin.objects.get(tg_id = user_id) == []:
        await message.answer("Ещё не дорос, пупсик")
        return
    if len(message.text.split()) != 2:
        await message.answer("Неверный формат команды")
        return
    new_admin_username = message.text.split()[1].replace("@", "")
    newadmin_id = User.objects.get(tg_id = new_admin_username).mesage_id
    if Admin.objects.get(tg_id = new_admin_username) != [] or SuperAdmin.objects.get(tg_id = new_admin_username) != [] :
        await message.answer(f"Да это же наш брат! Пользователь @{new_admin_username} уже админ")
        return
    if User.objects.get(tg_id = new_admin_username) != []:
        Admin.objects.create(tg_id = new_admin_username)
        await bot.send_message(newadmin_id, f"Поздравляю, ты стал админом таскабота!🥳", reply_markup=mk.adminMenu)
        await message.answer(f"Пользователь @{new_admin_username} теперь админ!🥳")
    else:
        await message.answer(f"Пользователь @{new_admin_username} не найден, возможно, не зарегистрирован.")

#+
@dp.message_handler(lambda message: message.text.startswith("/delete_admin"))
async def handle_delete_admin(message: types.Message):
    user_id = message.from_user.username
    if Admin.objects.get(tg_id = user_id) == [] and SuperAdmin.objects.get(tg_id = user_id) == []:
        await message.answer("Ещё не дорос, пупсик")
        return
    if len(message.text.split()) != 2:
        await message.answer("Неверный формат команды")
        return
    new_admin_username = message.text.split()[1].replace("@", "")
    newadmin_id = User.objects.get(tg_id = new_admin_username).mesage_id
    if Admin.objects.get(tg_id = new_admin_username) == [] and SuperAdmin.objects.get(tg_id = new_admin_username) == [] :
        await message.answer(f"Он и так не с нами! Пользователь @{new_admin_username} не может быть удалён, так как не \
является админом")
        return
    if User.objects.get(tg_id = new_admin_username) != []:
        Admin.objects.filter(tg_id = new_admin_username).delete()
        await bot.send_message(newadmin_id, f"Ты выписан из списка пидорасов (больше не админ)😭", reply_markup=mk.userMenu)
        await message.answer(f"Пользователь @{new_admin_username} больше не админ!😭")
    else:
        await message.answer(f"Пользователь @{new_admin_username} не найден, возможно, не зарегистрирован.")


@dp.message_handler()
async def all_(message: types.Message):
    if message.text.lower() == "жос":
        await message.answer("кий Добрыня Никитич")
    if message.text.lower() == "т":
        await message.answer("рубоеб Виталя")
async def on_startup(dp):
    asyncio.create_task(send_reminder())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)