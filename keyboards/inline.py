from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from datetime import datetime, timedelta
import calendar

def user_menu():
    """Меню для обычных пользователей"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✂️ Записаться', callback_data='booking')],
        [InlineKeyboardButton(text='📋 Мои записи', callback_data='my_bookings')],
        [InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')]
    ])
    return kb

def admin_menu():
    """Меню для администратора (без записи и моих записей)"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📩 Заявки на подтверждение', callback_data='admin_view_bookings')],
        [InlineKeyboardButton(text='📊 Все записи', callback_data='admin_all_bookings')],
        [InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')]
    ])
    return kb

def main_menu(user_id=None):
    """Главное меню - определяет роль пользователя"""
    if user_id and user_id == Config.ADMIN_ID:
        return admin_menu()
    return user_menu()

def masters_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    today = datetime.now().weekday()
    
    for master in Config.MASTERS:
        if not master.get('is_active', True):
            continue
            
        is_weekend = today in Config.WEEKEND_DAYS
        status = '🔴 (выходной)' if is_weekend else '🟢'
        
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{master['name']} {status}",
                callback_data=f"master_{master['id']}"
            )
        ])
    kb.inline_keyboard.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_menu')])
    return kb

def services_keyboard(master_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    master = Config.get_master_by_id(master_id)
    if not master:
        return masters_keyboard()
    
    service_ids = master.get('service_ids', [])
    for service in Config.SERVICES:
        if service['id'] in service_ids:
            kb.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{service['name']} - {service['price']}₽ ({service['duration']}мин)",
                    callback_data=f"service_{master_id}_{service['id']}"
                )
            ])
    kb.inline_keyboard.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_masters')])
    return kb

def dates_keyboard(master_id, service_id, month_offset=0):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    now = datetime.now()
    year = now.year
    month = now.month + month_offset
    if month > 12:
        month -= 12
        year += 1
    elif month < 1:
        month += 12
        year -= 1
    
    month_name = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][month-1]
    
    kb.inline_keyboard.append([
        InlineKeyboardButton(text=f'📅 {month_name} {year}', callback_data='ignore')
    ])
    
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    row = []
    for d in days:
        row.append(InlineKeyboardButton(text=d, callback_data='ignore'))
    kb.inline_keyboard.append(row)
    
    cal = calendar.monthcalendar(year, month)
    today = datetime.now().date()
    max_date = today + timedelta(days=Config.DAYS_IN_ADVANCE)
    
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=' ', callback_data='ignore'))
            else:
                date_obj = datetime(year, month, day).date()
                if date_obj < today or date_obj > max_date:
                    row.append(InlineKeyboardButton(text=f'❌{day}', callback_data='ignore'))
                elif date_obj.weekday() in Config.WEEKEND_DAYS:
                    row.append(InlineKeyboardButton(text=f'🚫{day}', callback_data='ignore'))
                else:
                    date_str = date_obj.strftime('%Y-%m-%d')
                    row.append(InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"date_{master_id}_{service_id}_{date_str}"
                    ))
        kb.inline_keyboard.append(row)
    
    nav_row = []
    nav_row.append(InlineKeyboardButton(text='◀️', callback_data=f'month_{master_id}_{service_id}_{month_offset-1}'))
    nav_row.append(InlineKeyboardButton(text='Сегодня', callback_data=f'month_{master_id}_{service_id}_0'))
    nav_row.append(InlineKeyboardButton(text='▶️', callback_data=f'month_{master_id}_{service_id}_{month_offset+1}'))
    kb.inline_keyboard.append(nav_row)
    
    kb.inline_keyboard.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_services')])
    return kb

def time_slots_keyboard(master_id, service_id, date_str):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    
    service = Config.get_service_by_id(service_id)
    if not service:
        return back_to_menu_button()
    
    duration = service['duration']
    
    from database import get_master_bookings
    bookings = get_master_bookings(master_id, date_str, 'confirmed')
    busy_times = [b['time'] for b in bookings]
    
    start_h = Config.WORK_START
    end_h = Config.WORK_END
    
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    current_min = now.hour * 60 + now.minute
    
    slot = start_h * 60
    while slot + duration <= end_h * 60:
        h = slot // 60
        m = slot % 60
        time_str = f"{h:02d}:{m:02d}"
        
        is_busy = time_str in busy_times
        
        if date_str == today:
            slot_min = h * 60 + m
            if slot_min <= current_min + 15:
                is_busy = True
        
        if not is_busy:
            kb.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🟢 {time_str}",
                    callback_data=f"time_{master_id}_{service_id}_{date_str}_{time_str}"
                )
            ])
        else:
            kb.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🔴 {time_str} (занято)",
                    callback_data='ignore'
                )
            ])
        
        slot += Config.BOOKING_INTERVAL
    
    if not kb.inline_keyboard:
        kb.inline_keyboard.append([
            InlineKeyboardButton(text="❌ Нет свободных слотов", callback_data='ignore')
        ])
    
    kb.inline_keyboard.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_dates')])
    return kb

def confirm_booking_keyboard(master_id, service_id, date_str, time_str):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'confirm_{master_id}_{service_id}_{date_str}_{time_str}'),
            InlineKeyboardButton(text='❌ Отмена', callback_data='back_to_menu')
        ]
    ])
    return kb

#def admin_booking_actions(booking_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'admin_confirm_{booking_id}'),
            InlineKeyboardButton(text='❌ Отклонить', callback_data=f'admin_reject_{booking_id}')
        ],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')]
    ])
    return kb

def my_bookings_keyboard(bookings):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for booking in bookings:
        status_emoji = '⏳' if booking['status'] == 'pending' else '✅' if booking['status'] == 'confirmed' else '❌'
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {booking['date']} {booking['time']} - {booking['master_name']}",
                callback_data=f"booking_detail_{booking['id']}"
            )
        ])
    kb.inline_keyboard.append([InlineKeyboardButton(text='🔙 В меню', callback_data='back_to_menu')])
    return kb

def booking_detail_keyboard(booking_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🗑 Отменить запись', callback_data=f'cancel_booking_{booking_id}')],
        [InlineKeyboardButton(text='🔙 Назад к списку', callback_data='back_to_my_bookings')],
        [InlineKeyboardButton(text='🔙 В меню', callback_data='back_to_menu')]
    ])
    return kb

def admin_bookings_keyboard(bookings):
    """Клавиатура для списка заявок - ТОЛЬКО ПРОСМОТР"""
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for booking in bookings:
        status_text = '⏳' if booking['status'] == 'pending' else '✅'
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{status_text} #{booking['id']} {booking['user_name']} {booking['date']} {booking['time']}",
                callback_data=f"admin_detail_{booking['id']}"
            )
        ])
    kb.inline_keyboard.append([InlineKeyboardButton(text='🔙 В админ-панель', callback_data='back_to_admin')])
    return kb

def contacts_keyboard(user_id=None):
    """Клавиатура для контактов с возвратом в нужное меню"""
    if user_id and user_id == Config.ADMIN_ID:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔙 В админ-панель', callback_data='back_to_admin')]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 В меню', callback_data='back_to_menu')]
    ])

def back_to_menu_button(user_id=None):
    """Универсальная кнопка назад"""
    if user_id and user_id == Config.ADMIN_ID:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔙 В админ-панель', callback_data='back_to_admin')]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 В меню', callback_data='back_to_menu')]
    ])

def admin_all_bookings_keyboard(bookings):
    """Клавиатура для просмотра всех записей"""
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Фильтры по статусу
    kb.inline_keyboard.append([
        InlineKeyboardButton(text='⏳ Ожидают', callback_data='admin_filter_pending'),
        InlineKeyboardButton(text='✅ Подтверждены', callback_data='admin_filter_confirmed'),
        InlineKeyboardButton(text='❌ Отменены', callback_data='admin_filter_cancelled')
    ])
    
    for booking in bookings[:20]:
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'cancelled': '❌',
            'done': '✔️'
        }.get(booking['status'], '📌')
        
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} #{booking['id']} {booking['user_name'][:12]} | {booking['date']} {booking['time']}",
                callback_data=f"admin_detail_{booking['id']}"
            )
        ])
    
    kb.inline_keyboard.append([InlineKeyboardButton(text='🔙 В админ-панель', callback_data='back_to_admin')])
    return kb

def admin_booking_actions(booking_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'admin_confirm_{booking_id}'),
            InlineKeyboardButton(text='❌ Отклонить', callback_data=f'admin_reject_{booking_id}')
        ],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')]
    ])
    return kb