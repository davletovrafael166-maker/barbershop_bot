from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.inline import (
    user_menu, admin_menu, contacts_keyboard, 
    back_to_menu_button, main_menu
)
from database import get_user_bookings
from config import Config

router = Router()

@router.message(Command('start'))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    
    # Проверяем, админ ли это
    if user_id == Config.ADMIN_ID:
        welcome_text = (
            "⚙️ <b>Админ-панель</b>\n\n"
            "Добро пожаловать в панель управления!\n"
            "Здесь вы можете управлять заявками клиентов."
        )
        await message.answer(welcome_text, reply_markup=admin_menu())
    else:
        welcome_text = (
            "✂️ <b>Добро пожаловать в наш барбершоп!</b>\n\n"
            "Я помогу вам:\n"
            "• Записаться к мастеру\n"
            "• Просмотреть ваши записи\n"
            "• Получить контакты\n\n"
            "Выберите действие ниже 👇"
        )
        await message.answer(welcome_text, reply_markup=user_menu())

@router.callback_query(F.data == 'back_to_menu')
async def back_to_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        text = "⚙️ <b>Админ-панель</b>\n\nУправляйте заявками клиентов."
        await callback.message.edit_text(text, reply_markup=admin_menu())
    else:
        text = "✂️ <b>Главное меню</b>\n\nВыберите действие:"
        await callback.message.edit_text(text, reply_markup=user_menu())
    
    await callback.answer()

@router.callback_query(F.data == 'contacts')
async def show_contacts(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    text = (
        f"📞 <b>{Config.SHOP_NAME}</b>\n\n"
        f"📍 <b>Адрес:</b> {Config.SHOP_ADDRESS}\n"
        f"⏰ <b>Режим работы:</b> {Config.SHOP_WORK_HOURS}\n"
        f"📱 <b>Телефон:</b> {Config.SHOP_PHONE}\n"
        f"📸 <b>Instagram:</b> @{Config.SHOP_INSTAGRAM}\n\n"
        f"{Config.SHOP_DESCRIPTION}\n\n"
        "Записаться можно прямо в боте!"
    )
    
    await callback.message.edit_text(text, reply_markup=contacts_keyboard(user_id))
    await callback.answer()

@router.callback_query(F.data == 'my_bookings')
async def my_bookings(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Если админ пытается зайти в мои записи - перенаправляем в админку
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Для админов доступна только админ-панель", show_alert=True)
        return
    
    bookings = get_user_bookings(user_id)
    
    if not bookings:
        await callback.message.edit_text(
            "📋 <b>У вас нет активных записей</b>\n\n"
            "Хотите записаться? Используйте кнопку ✂️ Записаться",
            reply_markup=back_to_menu_button(user_id)
        )
        await callback.answer()
        return
    
    from keyboards.inline import my_bookings_keyboard
    text = "📋 <b>Ваши записи:</b>\n\n"
    for b in bookings:
        status_text = {
            'pending': '⏳ Ожидает подтверждения',
            'confirmed': '✅ Подтверждена',
            'cancelled': '❌ Отменена',
            'done': '✔️ Выполнена'
        }.get(b['status'], b['status'])
        text += f"▫️ <b>{b['date']}</b> в <b>{b['time']}</b>\n"
        text += f"   👤 {b['master_name']} | {b['service_name']} - {b['service_price']}₽\n"
        text += f"   Статус: {status_text}\n\n"
    
    await callback.message.edit_text(text, reply_markup=my_bookings_keyboard(bookings))
    await callback.answer()

@router.callback_query(F.data.startswith('booking_detail_'))
async def booking_detail(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    booking_id = int(callback.data.split('_')[2])
    from database import get_booking
    from keyboards.inline import booking_detail_keyboard, back_to_menu_button
    
    booking = get_booking(booking_id)
    if not booking:
        await callback.answer("Запись не найдена")
        return
    
    if booking['user_id'] != user_id:
        await callback.answer("⛔️ Это не ваша запись")
        return
    
    # ПРОВЕРЯЕМ СТАТУС - если запись отменена, показываем кнопку "В меню"
    if booking['status'] == 'cancelled':
        status_text = '❌ Отменена'
        await callback.message.edit_text(
            f"❌ <b>Запись отменена</b>\n\n"
            f"👤 <b>Мастер:</b> {booking['master_name']}\n"
            f"✂️ <b>Услуга:</b> {booking['service_name']}\n"
            f"💰 <b>Цена:</b> {booking['service_price']}₽\n"
            f"📅 <b>Дата:</b> {booking['date']}\n"
            f"🕐 <b>Время:</b> {booking['time']}\n"
            f"📊 <b>Статус:</b> {status_text}\n",
            reply_markup=back_to_menu_button(user_id)
        )
        await callback.answer()
        return
    
    status_text = {
        'pending': '⏳ Ожидает подтверждения',
        'confirmed': '✅ Подтверждена',
        'cancelled': '❌ Отменена',
        'done': '✔️ Выполнена'
    }.get(booking['status'], booking['status'])
    
    text = (
        f"📋 <b>Детали записи</b>\n\n"
        f"👤 <b>Мастер:</b> {booking['master_name']}\n"
        f"✂️ <b>Услуга:</b> {booking['service_name']}\n"
        f"💰 <b>Цена:</b> {booking['service_price']}₽\n"
        f"📅 <b>Дата:</b> {booking['date']}\n"
        f"🕐 <b>Время:</b> {booking['time']}\n"
        f"📊 <b>Статус:</b> {status_text}\n"
    )
    
    # ПОКАЗЫВАЕМ КНОПКУ ОТМЕНЫ ТОЛЬКО ДЛЯ АКТИВНЫХ ЗАПИСЕЙ
    if booking['status'] in ['pending', 'confirmed']:
        await callback.message.edit_text(text, reply_markup=booking_detail_keyboard(booking_id))
    else:
        await callback.message.edit_text(text, reply_markup=back_to_menu_button(user_id))
    
    await callback.answer()

@router.callback_query(F.data.startswith('cancel_booking_'))
async def cancel_booking(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель для управления", show_alert=True)
        return
    
    booking_id = int(callback.data.split('_')[2])
    from database import get_booking, delete_booking_permanently
    from keyboards.inline import back_to_menu_button
    
    booking = get_booking(booking_id)
    if not booking:
        await callback.answer("Запись не найдена")
        return
    
    if booking['user_id'] != user_id:
        await callback.answer("⛔️ Это не ваша запись")
        return
    
    # ПОЛНОСТЬЮ УДАЛЯЕМ ЗАПИСЬ
    delete_booking_permanently(booking_id)
    
    await callback.message.edit_text(
        f"❌ <b>Запись отменена</b>\n\n"
        f"Ваша запись к {booking['master_name']} на {booking['date']} в {booking['time']} отменена.",
        reply_markup=back_to_menu_button(user_id)
    )
    
    await callback.bot.send_message(
        Config.ADMIN_ID,
        f"🗑 Клиент отменил запись #{booking_id}\n"
        f"👤 {booking['user_name']}\n"
        f"📅 {booking['date']} {booking['time']}"
    )
    
    await callback.answer()
@router.callback_query(F.data == 'back_to_my_bookings')
async def back_to_my_bookings(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    bookings = get_user_bookings(user_id)
    
    if not bookings:
        await callback.message.edit_text(
            "📋 <b>У вас нет активных записей</b>",
            reply_markup=back_to_menu_button(user_id)
        )
        await callback.answer()
        return
    
    from keyboards.inline import my_bookings_keyboard
    text = "📋 <b>Ваши записи:</b>\n\n"
    for b in bookings:
        status_text = {
            'pending': '⏳ Ожидает подтверждения',
            'confirmed': '✅ Подтверждена',
            'cancelled': '❌ Отменена',
            'done': '✔️ Выполнена'
        }.get(b['status'], b['status'])
        text += f"▫️ <b>{b['date']}</b> в <b>{b['time']}</b>\n"
        text += f"   👤 {b['master_name']} | {b['service_name']} - {b['service_price']}₽\n"
        text += f"   Статус: {status_text}\n\n"
    
    await callback.message.edit_text(text, reply_markup=my_bookings_keyboard(bookings))
    await callback.answer()