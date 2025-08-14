from django.core.management.base import BaseCommand
from telegram_bot.utils import send_all_reports_direct
from datetime import datetime
import pytz



class Command(BaseCommand):
	help = "Send to every user their full outage reports through telegram bot"

	def handle(self, *args, **options):
		tz = pytz.timezone("Asia/Tehran")
		now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
		self.stdout.write(f"[{now}] Starting report sending...")

		send_all_reports_direct()

		now = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
		self.stdout.write(f"[{now}] Full reports have been sent to users.")
