from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline import admin_booking_actions, admin_bookings_keyboard, back_to_menu_button, admin_menu
from database import get_all_bookings, get_booking, update_booking_status
from config import Config

router = Router()

async def notify_admin_about_booking(bot, booking_id):
    """Отправка уведомления админу о новой заявке (БЕЗ КНОПОК, со ссылкой на профиль)"""
    from database import get_booking
    booking = get_booking(booking_id)
    if not booking:
        return
    
    # Ссылка на профиль клиента в Telegram
    user_link = f"tg://user?id={booking['user_id']}"
    
    text = (
        "📩 НОВАЯ ЗАЯВКА НА ЗАПИСЬ!\n"
        "═══════════════════════════════\n\n"
        f"🆔 Заявка: #{booking['id']}\n"
        f"👤 Клиент: <a href='{user_link}'>{booking['user_name']}</a>\n"
        f"📱 Телефон: {booking['user_phone'] or 'Не указан'}\n"
        f"👤 Мастер: {booking['master_name']}\n"
        f"✂️ Услуга: {booking['service_name']}\n"
        f"💰 Цена: {booking['service_price']}₽\n"
        f"📅 Дата: {booking['date']}\n"
        f"🕐 Время: {booking['time']}\n"
        f"⏳ Статус: Ожидает подтверждения\n\n"
        "Для управления заявками используйте админ-панель в боте."
    )
    
    await bot.send_message(Config.ADMIN_ID, text)
        
    

@router.callback_query(F.data == 'back_to_admin')
async def back_to_admin(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещен")
        return
    
    text = "⚙️ <b>Админ-панель</b>\n\nУправляйте заявками клиентов."
    await callback.message.edit_text(text, reply_markup=admin_menu())
    await callback.answer()

@router.callback_query(F.data == 'admin_view_bookings')
async def admin_view_bookings(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещен")
        return
    
    bookings = get_all_bookings('pending')
    
    if not bookings:
        await callback.message.edit_text(
            "📭 <b>Нет заявок, ожидающих подтверждения.</b>",
            reply_markup=admin_menu()
        )
        await callback.answer()
        return
    
    text = f"📩 <b>Ожидают подтверждения ({len(bookings)}):</b>\n\n"
    for b in bookings[:10]:
        text += f"#{b['id']} {b['user_name']} | {b['date']} {b['time']}\n"
    
    if len(bookings) > 10:
        text += f"\n...и еще {len(bookings) - 10} заявок"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_bookings_keyboard(bookings[:10])
    )
    await callback.answer()

@router.callback_query(F.data == 'admin_all_bookings')
async def admin_all_bookings(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещен")
        return
    
    bookings = get_all_bookings()
    
    if not bookings:
        await callback.message.edit_text(
            "📭 <b>Нет записей в системе.</b>",
            reply_markup=admin_menu()
        )
        await callback.answer()
        return
    
    pending = len([b for b in bookings if b['status'] == 'pending'])
    confirmed = len([b for b in bookings if b['status'] == 'confirmed'])
    cancelled = len([b for b in bookings if b['status'] == 'cancelled'])
    done = len([b for b in bookings if b['status'] == 'done'])
    
    text = (
        "📊 <b>Все записи</b>\n\n"
        f"📌 <b>Всего:</b> {len(bookings)}\n"
        f"⏳ Ожидают: {pending}\n"
        f"✅ Подтверждены: {confirmed}\n"
        f"❌ Отменены: {cancelled}\n"
        f"✔️ Выполнены: {done}\n\n"
        "<b>Последние записи:</b>\n"
    )
    
    for b in bookings[:10]:
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'cancelled': '❌',
            'done': '✔️'
        }.get(b['status'], '📌')
        text += f"{status_emoji} #{b['id']} {b['user_name'][:12]} | {b['date']} {b['time']}\n"
    
    if len(bookings) > 10:
        text += f"\n...и еще {len(bookings) - 10} записей"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_bookings_keyboard(bookings[:20])
    )
    await callback.answer()

@router.callback_query(F.data.startswith('admin_filter_'))
async def admin_filter_bookings(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещен")
        return
    
    status = callback.data.split('_')[2]
    status_map = {
        'pending': '⏳ Ожидают',
        'confirmed': '✅ Подтверждены',
        'cancelled': '❌ Отменены'
    }
    
    bookings = get_all_bookings(status)
    
    if not bookings:
        await callback.message.edit_text(
            f"📭 <b>Нет записей со статусом: {status_map.get(status, status)}</b>",
            reply_markup=admin_menu()
        )
        await callback.answer()
        return
    
    text = f"📊 <b>{status_map.get(status, status)} ({len(bookings)}):</b>\n\n"
    for b in bookings[:20]:
        text += f"#{b['id']} {b['user_name'][:12]} | {b['date']} {b['time']}\n"
    
    if len(bookings) > 20:
        text += f"\n...и еще {len(bookings) - 20} записей"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_bookings_keyboard(bookings[:20])
    )
    await callback.answer()

@router.callback_query(F.data.startswith('admin_confirm_'))
async def admin_confirm(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещен")
        return
    
    booking_id = int(callback.data.split('_')[2])
    booking = get_booking(booking_id)
    
    if not booking:
        await callback.answer("Запись не найдена")
        return
    
    update_booking_status(booking_id, 'confirmed')
    
    await callback.message.edit_text(
        f"✅ Запись #{booking_id} подтверждена!",
        reply_markup=admin_menu()
    )
    
    if Config.NOTIFY_CLIENT_ON_CONFIRM:
        await callback.bot.send_message(
            booking['user_id'],
            f"✅ <b>Ваша запись подтверждена!</b>\n\n"
            f"👤 <b>Мастер:</b> {booking['master_name']}\n"
            f"✂️ <b>Услуга:</b> {booking['service_name']} - {booking['service_price']}₽\n"
            f"📅 <b>Дата:</b> {booking['date']}\n"
            f"🕐 <b>Время:</b> {booking['time']}\n\n"
            "Ждем вас! 🤝"
        )
    
    master_tg_id = Config.get_master_telegram_id(booking['master_id'])
    if master_tg_id:
        await callback.bot.send_message(
            master_tg_id,
            f"📅 <b>Новая запись!</b>\n\n"
            f"👤 <b>Клиент:</b> {booking['user_name']}\n"
            f"✂️ <b>Услуга:</b> {booking['service_name']} - {booking['service_price']}₽\n"
            f"📅 <b>Дата:</b> {booking['date']}\n"
            f"🕐 <b>Время:</b> {booking['time']}\n\n"
            "Клиент подтвержден! ✅"
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith('admin_reject_'))
async def admin_reject(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещен")
        return
    
    booking_id = int(callback.data.split('_')[2])
    booking = get_booking(booking_id)
    
    if not booking:
        await callback.answer("Запись не найдена")
        return
    
    update_booking_status(booking_id, 'cancelled')
    
    await callback.message.edit_text(
        f"❌ Запись #{booking_id} отклонена.",
        reply_markup=admin_menu()
    )
    
    await callback.bot.send_message(
        booking['user_id'],
        f"❌ <b>Ваша запись отклонена</b>\n\n"
        f"К сожалению, администратор отклонил вашу запись на {booking['date']} в {booking['time']}.\n"
        f"Попробуйте записаться на другое время."
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith('admin_detail_'))
async def admin_booking_detail(callback: CallbackQuery):
    if callback.from_user.id != Config.ADMIN_ID:
        await callback.answer("⛔️ Доступ запрещен")
        return
    
    booking_id = int(callback.data.split('_')[2])
    booking = get_booking(booking_id)
    
    if not booking:
        await callback.answer("Запись не найдена")
        return
    
    status_text = {
        'pending': '⏳ Ожидает подтверждения',
        'confirmed': '✅ Подтверждена',
        'cancelled': '❌ Отменена',
        'done': '✔️ Выполнена'
    }.get(booking['status'], booking['status'])
    
    text = (
        f"📋 <b>Детали заявки #{booking['id']}</b>\n\n"
        f"👤 <b>Клиент:</b> {booking['user_name']} (ID: {booking['user_id']})\n"
        f"📱 <b>Телефон:</b> {booking['user_phone'] or 'Не указан'}\n"
        f"👤 <b>Мастер:</b> {booking['master_name']}\n"
        f"✂️ <b>Услуга:</b> {booking['service_name']} - {booking['service_price']}₽\n"
        f"⏱ <b>Длительность:</b> {booking['service_duration']} мин\n"
        f"📅 <b>Дата:</b> {booking['date']}\n"
        f"🕐 <b>Время:</b> {booking['time']}\n"
        f"📊 <b>Статус:</b> {status_text}\n"
    )
    
    if booking['confirmed_at']:
        text += f"✅ <b>Подтверждена:</b> {booking['confirmed_at']}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_booking_actions(booking_id)
    )
    await callback.answer()