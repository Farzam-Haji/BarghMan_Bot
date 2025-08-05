# this a production testing file
import sys
import os
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BarghMan_Bot.settings")
django.setup()


from accounts.models import TelegramUser
from telegram_bot.utils import send_telegram_user_reports
user = TelegramUser.objects.filter(username="@Oceanus_95").first()
send_telegram_user_reports(user)