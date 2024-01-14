from aiogram.types import CallbackQuery, Message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot_create import bot
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from keyboards.kb_cancel import mkp_cancel
import smtplib
import asyncio
import random

global is_sending
is_sending = False

class Startwork(StatesGroup):
    credentials = State()
    theme = State()
    text = State()
    names = State()
    count_mails = State()
    recipients = State()


router_cb_start = Router()

@router_cb_start.callback_query(F.data.startswith('call.'))
async def start_working(call: CallbackQuery, state: FSMContext):
    if call.data == 'call.startwork':
        await call.message.edit_text(text='<b>Отлично, введите логин:пароль от аккаунтов гмайл на каждой новой строке</b>', 
                                     parse_mode='html', reply_markup=mkp_cancel)
        await state.set_state(Startwork.credentials)
    if call.data == 'call.cancel':
        await state.clear()
        await call.message.edit_text(text='<b>Действие было успешно отменено</b>', parse_mode='html')

@router_cb_start.message(Startwork.credentials)
async def input_credentials(msg: Message, state: FSMContext):
    await state.update_data(credentials=msg.text.strip().split('\n'))
    await msg.answer('<b>Отлично, теперь введите тему для рассылки: \nНапример: \nRegarding reservations in September.</b>',
                     parse_mode='html', reply_markup=mkp_cancel)
    await state.set_state(Startwork.theme)

@router_cb_start.message(Startwork.theme)
async def input_theme(msg: Message, state: FSMContext):
    await state.update_data(theme=msg.text)
    await msg.answer(f'<b>Отлично, тема: {msg.text}\nТеперь укажите текст рассылки.</b>', parse_mode='html', reply_markup=mkp_cancel)
    await state.set_state(Startwork.text)

@router_cb_start.message(Startwork.text)
async def input_count(msg: Message, state: FSMContext):
    await state.update_data(text=msg.text)
    await msg.answer('<b>Отлично, теперь напишите список имён, каждое имя на отдельной строке</b>',
                     parse_mode='html', reply_markup=mkp_cancel)
    await state.set_state(Startwork.names)

@router_cb_start.message(Startwork.names)
async def input_names(msg: Message, state: FSMContext):
    await state.update_data(names=msg.text)
    await msg.answer('<b>Отлично, теперь напишите (в цифрах) какое кол-во писем отправлять с 1 аккаунта\n'
                     'Если укажите по 150 на 2 аккаунта. То общее кол-во отправленных сообщений будет 300</b>',
                     parse_mode='html', reply_markup=mkp_cancel)
    await state.set_state(Startwork.count_mails)
    
@router_cb_start.message(Startwork.count_mails)
async def input_count(msg: Message, state: FSMContext):
    await state.update_data(count=msg.text)
    await msg.answer('<b>Отлично, теперь пришлите список получателей в формате .txt</b>',
                     parse_mode='html', reply_markup=mkp_cancel)
    await state.set_state(Startwork.recipients)

@router_cb_start.message(Startwork.recipients)
async def input_recipients(msg: Message, state: FSMContext):
    text = msg.text
    if msg.document:
        file_id = msg.document.file_id
        file = await bot.get_file(file_id)
        content = await bot.download_file(file.file_path)
        content_str = content.read().decode('utf-8')
        text = content_str.strip()
    recipients_list = text.strip().split('\n')
    await state.update_data(recipients=recipients_list)
    data = await state.get_data()
    emailpass = data.get('credentials')
    theme = data.get('theme')
    text = data.get('text')
    names = data.get('names')
    count = data.get('count')
    try:
        await send_to_emails(emailpass, theme, text, names, recipients_list, count, msg)
    except Exception as _ex:
        await msg.answer('<b>ERROR: ', _ex)
        await state.clear()
    await state.clear()

async def send_email(email, password, recipient, theme, text, name, msg):
    try:
        # Создать объект SMTP для подключения к серверу Gmail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()  # Приветственное сообщение сервера
            server.starttls()  # Установить защищенное соединение
            server.ehlo()  # Приветственное сообщение сервера (после установки защищенного соединения)
            server.login(email, password)  # Аутентификация на сервере SMTP

            # Создать сообщение
            message = MIMEMultipart('alternative')
            message['From'] = email
            message['To'] = recipient
            message['Subject'] = random.choice(theme)
            text = text
            name = name
            text = text + f'\n\nRegards, {name}'
            # Создать версию HTML сообщения
            message.attach(MIMEText(text, 'plain'))

            # Отправить сообщение
            server.send_message(message)

            return recipient

    except Exception as e:
        if 'quota' in str(e):
            await msg.answer(f'<b>❌ Превышена квота по аккаунту {email}\n'
                             f'Email на котором случилась ошибка: {recipient}</b>', parse_mode='html')
        await msg.answer(f'❌ Произошла ошибка во время выполнения рассылки: {e}')

    return None


async def send_to_emails(accounts, theme, text, names, recipients, count, msg):
    global is_sending
    if is_sending:
        await msg.answer('<b>Бот сейчас занят.</b>', parse_mode='html')
        return
    is_sending = True  # Установка флага, что рассылка запущена
    await msg.answer('<b>Начинаем рассылку!</b>', parse_mode='html', )
    max_send = int(count)
    count = 0
    names = names.split('\n')
    try:
        for account in accounts:
            if recipients == None:
                await msg.answer('<b>Закончились почты</b>', parse_mode='html')
                break

            email, password = account.split(':')
            for recipient in recipients[:max_send]:
                try:
                    name = names[count]
                    await send_email(email, password, recipient, theme, text, name, msg)
                    await msg.answer(f'<b>[✅Успех]: Сообщение было отправлено - {recipient} от {email}</b>', parse_mode='html')
                    await asyncio.sleep(3)  # Задержка в 5 секунд между отправкой писем
                except Exception as e:
                    await msg.answer(f'<b>[❌ Ошибка] - {e}</b>', parse_mode='html')
            count += 1
            recipients = recipients[max_send:]
    except Exception as e:
        await msg.answer(f'<b> Error: {e}</b>', parse_mode='html')
    await msg.answer('<b>Рассылка завершена!</b>', parse_mode='html')
    is_sending = False  # Сброс флага, что рассылка завершена
