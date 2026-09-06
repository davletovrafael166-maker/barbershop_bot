import os
import json
from dotenv import load_dotenv

load_dotenv()

class Config:
    # === БОТ ===
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
    
    # === ПРОКСИ (ДОБАВЬТЕ ЭТО) ===
    PROXY_URL = os.getenv('PROXY_URL', None)  # например: socks5://127.0.0.1:1080
    
    # === ИНФО БАРБЕРШОПА ===
    SHOP_NAME = os.getenv('SHOP_NAME', 'Барбершоп')
    SHOP_ADDRESS = os.getenv('SHOP_ADDRESS', '')
    SHOP_PHONE = os.getenv('SHOP_PHONE', '')
    SHOP_WORK_HOURS = os.getenv('SHOP_WORK_HOURS', '10:00 - 22:00')
    SHOP_INSTAGRAM = os.getenv('SHOP_INSTAGRAM', '')
    SHOP_DESCRIPTION = os.getenv('SHOP_DESCRIPTION', '')
    
    # === УСЛУГИ ===
    SERVICES = json.loads(os.getenv('SERVICES', '[]'))
    
    # === МАСТЕРА ===
    MASTERS = json.loads(os.getenv('MASTERS', '[]'))
    MASTER_IDS = json.loads(os.getenv('MASTER_IDS', '{}'))
    
    # === НАСТРОЙКИ ЗАПИСИ ===
    BOOKING_INTERVAL = int(os.getenv('BOOKING_INTERVAL', 30))
    WORK_START = int(os.getenv('WORK_START', 10))
    WORK_END = int(os.getenv('WORK_END', 22))
    DAYS_IN_ADVANCE = int(os.getenv('DAYS_IN_ADVANCE', 14))
    WEEKEND_DAYS = json.loads(os.getenv('WEEKEND_DAYS', '[6]'))
    
    # === УВЕДОМЛЕНИЯ ===
    NOTIFY_ADMIN_ON_BOOKING = os.getenv('NOTIFY_ADMIN_ON_BOOKING', 'true').lower() == 'true'
    NOTIFY_CLIENT_ON_CONFIRM = os.getenv('NOTIFY_CLIENT_ON_CONFIRM', 'true').lower() == 'true'
    REMIND_HOURS = int(os.getenv('REMIND_HOURS', 2))
    
    # === БАЗА ДАННЫХ ===
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///barbershop.db')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    @classmethod
    def get_master_by_id(cls, master_id):
        for master in cls.MASTERS:
            if master['id'] == master_id:
                return master
        return None
    
    @classmethod
    def get_service_by_id(cls, service_id):
        for service in cls.SERVICES:
            if service['id'] == service_id:
                return service
        return None
    
    @classmethod
    def get_master_telegram_id(cls, master_id):
        return cls.MASTER_IDS.get(str(master_id))