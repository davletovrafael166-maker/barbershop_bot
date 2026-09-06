from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import get_bookings_for_reminder, mark_reminder_sent
from config import Config

scheduler = None

def start_scheduler(bot):
    global scheduler
    scheduler = AsyncIOScheduler()
    
    # Проверка каждые 10 минут
    scheduler.add_job(
        check_reminders,
        CronTrigger(minute='*/10'),
        args=[bot],
        id='reminder_job'
    )
    
    scheduler.start()
    print("⏰ Планировщик напоминаний запущен!")

async def check_reminders(bot):
    """Проверяет и отправляет напоминания за 2 часа до записи"""
    try:
        bookings = get_bookings_for_reminder(Config.REMIND_HOURS)
        
        for booking in bookings:
            try:
                await bot.send_message(
                    booking['user_id'],
                    f"⏰ <b>Напоминание!</b>\n\n"
                    f"У вас запись к <b>{booking['master_name']}</b>\n"
                    f"📅 {booking['date']} в {booking['time']}\n"
                    f"✂️ {booking['service_name']} - {booking['service_price']}₽\n\n"
                    f"📍 {Config.SHOP_ADDRESS}\n"
                    f"📞 {Config.SHOP_PHONE}\n\n"
                    "Ждем вас! 🤝"
                )
                
                mark_reminder_sent(booking['id'])
                
            except Exception as e:
                print(f"Ошибка отправки напоминания: {e}")
                
    except Exception as e:
        print(f"Ошибка в планировщике: {e}")