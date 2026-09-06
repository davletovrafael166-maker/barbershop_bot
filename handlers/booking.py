from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.inline import (
    masters_keyboard, services_keyboard, dates_keyboard, 
    time_slots_keyboard, confirm_booking_keyboard, back_to_menu_button
)
from database import (
    get_temp_data, save_temp_data, delete_temp_data, 
    add_booking, get_master_bookings
)
from config import Config
from datetime import datetime

router = Router()

# ==================== ШАГ 1: ВЫБОР МАСТЕРА ====================

@router.callback_query(F.data == 'booking')
async def start_booking(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Админы не могут записываться через эту кнопку
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Администратор не может записаться как клиент", show_alert=True)
        return
    
    await callback.message.edit_text(
        "✂️ <b>Запись к мастеру</b>\n\n"
        "Шаг 1: Выберите мастера 👇",
        reply_markup=masters_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == 'back_to_masters')
async def back_to_masters(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    delete_temp_data(callback.from_user.id)
    await callback.message.edit_text(
        "✂️ <b>Выбор мастера</b>\n\n"
        "Выберите мастера:",
        reply_markup=masters_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith('master_'))
async def select_master(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    master_id = int(callback.data.split('_')[1])
    master = Config.get_master_by_id(master_id)
    
    if not master:
        await callback.answer("Мастер не найден")
        return
    
    # Проверяем, работает ли мастер сегодня
    today = datetime.now().weekday()
    if today in Config.WEEKEND_DAYS:
        await callback.answer("❌ Сегодня выходной день!", show_alert=True)
        return
    
    # Сохраняем выбранного мастера
    save_temp_data(callback.from_user.id, {'master_id': master_id})
    
    await callback.message.edit_text(
        f"👤 <b>Мастер: {master['name']}</b>\n\n"
        "Шаг 2: Выберите услугу 👇",
        reply_markup=services_keyboard(master_id)
    )
    await callback.answer()


# ==================== ШАГ 2: ВЫБОР УСЛУГИ ====================

@router.callback_query(F.data == 'back_to_services')
async def back_to_services(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    data = get_temp_data(callback.from_user.id)
    if not data or 'master_id' not in data:
        await callback.message.edit_text(
            "Ошибка, начните сначала",
            reply_markup=masters_keyboard()
        )
        return
    
    master_id = data['master_id']
    await callback.message.edit_text(
        "Шаг 2: Выберите услугу 👇",
        reply_markup=services_keyboard(master_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith('service_'))
async def select_service(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    parts = callback.data.split('_')
    master_id = int(parts[1])
    service_id = int(parts[2])
    
    service = Config.get_service_by_id(service_id)
    if not service:
        await callback.answer("Услуга не найдена")
        return
    
    # Сохраняем ID услуги
    data = get_temp_data(callback.from_user.id) or {}
    data['service_id'] = service_id
    save_temp_data(callback.from_user.id, data)
    
    await callback.message.edit_text(
        f"📅 <b>Выберите дату</b>\n\n"
        f"Услуга: {service['name']} - {service['price']}₽\n"
        "Шаг 3: Выберите день 👇",
        reply_markup=dates_keyboard(master_id, service_id)
    )
    await callback.answer()


# ==================== ШАГ 3: ВЫБОР ДАТЫ ====================

@router.callback_query(F.data.startswith('month_'))
async def change_month(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    parts = callback.data.split('_')
    master_id = int(parts[1])
    service_id = int(parts[2])
    month_offset = int(parts[3])
    
    await callback.message.edit_reply_markup(
        reply_markup=dates_keyboard(master_id, service_id, month_offset)
    )
    await callback.answer()


@router.callback_query(F.data == 'back_to_dates')
async def back_to_dates(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    data = get_temp_data(callback.from_user.id)
    if not data:
        await callback.answer("Ошибка, начните сначала")
        return
    
    master_id = data.get('master_id')
    service_id = data.get('service_id')
    
    if not master_id or not service_id:
        await callback.answer("Ошибка данных, начните сначала")
        return
    
    await callback.message.edit_text(
        "📅 <b>Выберите дату</b>\n\n"
        "Шаг 3: Выберите день 👇",
        reply_markup=dates_keyboard(master_id, service_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith('date_'))
async def select_date(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    parts = callback.data.split('_')
    master_id = int(parts[1])
    service_id = int(parts[2])
    date_str = parts[3]
    
    # Сохраняем дату
    data = get_temp_data(callback.from_user.id) or {}
    data['date'] = date_str
    save_temp_data(callback.from_user.id, data)
    
    await callback.message.edit_text(
        f"🕐 <b>Выберите время</b>\n\n"
        f"Дата: {date_str}\n"
        "Шаг 4: Выберите свободный слот 👇",
        reply_markup=time_slots_keyboard(master_id, service_id, date_str)
    )
    await callback.answer()


# ==================== ШАГ 4: ВЫБОР ВРЕМЕНИ ====================

@router.callback_query(F.data.startswith('time_'))
async def select_time(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Используйте админ-панель", show_alert=True)
        return
    
    parts = callback.data.split('_')
    master_id = int(parts[1])
    service_id = int(parts[2])
    date_str = parts[3]
    time_str = parts[4]
    
    # ПРОВЕРКА: не занято ли это время прямо сейчас
    bookings = get_master_bookings(master_id, date_str, 'confirmed')
    busy_times = [b['time'] for b in bookings]
    
    if time_str in busy_times:
        await callback.answer("❌ Это время уже занято! Выберите другое.", show_alert=True)
        # Обновляем клавиатуру, показывая актуальные слоты
        await callback.message.edit_text(
            f"🕐 <b>Выберите время</b>\n\n"
            f"Дата: {date_str}\n"
            "Некоторые слоты уже заняты. Выберите свободный 👇",
            reply_markup=time_slots_keyboard(master_id, service_id, date_str)
        )
        return
    
    # Сохраняем время
    data = get_temp_data(callback.from_user.id) or {}
    data['time'] = time_str
    save_temp_data(callback.from_user.id, data)
    
    service = Config.get_service_by_id(service_id)
    master = Config.get_master_by_id(master_id)
    
    if not service or not master:
        await callback.answer("Ошибка данных")
        return
    
    text = (
        "✂️ <b>Подтверждение записи</b>\n\n"
        f"👤 <b>Мастер:</b> {master['name']}\n"
        f"✂️ <b>Услуга:</b> {service['name']}\n"
        f"💰 <b>Цена:</b> {service['price']}₽\n"
        f"⏱ <b>Длительность:</b> {service['duration']} мин\n"
        f"📅 <b>Дата:</b> {date_str}\n"
        f"🕐 <b>Время:</b> {time_str}\n\n"
        "Подтвердите запись или отмените:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=confirm_booking_keyboard(master_id, service_id, date_str, time_str)
    )
    await callback.answer()


# ==================== ШАГ 5: ПОДТВЕРЖДЕНИЕ ЗАПИСИ ====================

@router.callback_query(F.data.startswith('confirm_'))
async def confirm_booking(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # Админы не могут записываться
    if user_id == Config.ADMIN_ID:
        await callback.answer("⛔️ Администратор не может записаться как клиент", show_alert=True)
        return
    
    parts = callback.data.split('_')
    master_id = int(parts[1])
    service_id = int(parts[2])
    date_str = parts[3]
    time_str = parts[4]
    
    user_name = callback.from_user.full_name
    user_phone = None
    
    service = Config.get_service_by_id(service_id)
    master = Config.get_master_by_id(master_id)
    
    if not service or not master:
        await callback.answer("Ошибка: данные не найдены")
        return
    
    # Проверяем, не занято ли время (на случай, если кто-то успел записаться)
    bookings = get_master_bookings(master_id, date_str, 'confirmed')
    busy_times = [b['time'] for b in bookings]
    
    if time_str in busy_times:
        await callback.answer("❌ Это время уже занято. Выберите другое.", show_alert=True)
        await callback.message.edit_text(
            "🕐 <b>Выберите другое время</b>\n\n"
            "Этот слот уже занят. Выберите другой:",
            reply_markup=time_slots_keyboard(master_id, service_id, date_str)
        )
        return
    
    # Создаем запись со статусом 'pending'
    booking_id = add_booking(
        user_id, user_name, user_phone,
        master_id, master['name'],
        service_id, service['name'], service['price'], service['duration'],
        date_str, time_str
    )
    
    # Очищаем временные данные
    delete_temp_data(user_id)
    
    # Отправляем клиенту подтверждение
    await callback.message.edit_text(
        "✅ <b>Заявка отправлена!</b>\n\n"
        f"Ваша запись к <b>{master['name']}</b> на {date_str} в {time_str}\n"
        f"Услуга: {service['name']} - {service['price']}₽\n\n"
        "⏳ Ожидайте подтверждения администратора.\n"
        "Вам придет уведомление, когда запись будет подтверждена.",
        reply_markup=back_to_menu_button(user_id)
    )
    
    # Уведомление админу
    if Config.NOTIFY_ADMIN_ON_BOOKING:
        from handlers.admin import notify_admin_about_booking
        await notify_admin_about_booking(callback.bot, booking_id)
    
    await callback.answer()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ====================

@router.callback_query(F.data == 'ignore')
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data == 'back_to_menu_from_booking')
async def back_to_menu_from_booking(callback: CallbackQuery):
    user_id = callback.from_user.id
    delete_temp_data(user_id)
    
    from keyboards.inline import main_menu
    if user_id == Config.ADMIN_ID:
        text = "⚙️ <b>Админ-панель</b>\n\nУправляйте заявками клиентов."
        await callback.message.edit_text(text, reply_markup=admin_menu())
    else:
        text = "✂️ <b>Главное меню</b>\n\nВыберите действие:"
        await callback.message.edit_text(text, reply_markup=main_menu(user_id))
    
    await callback.answer()