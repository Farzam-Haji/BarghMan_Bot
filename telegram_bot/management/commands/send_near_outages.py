from django.core.management.base import BaseCommand
from telegram_bot.utils import send_near_reports_direct
from datetime import datetime




class Command(BaseCommand):
	help = "Send to every user their near outage reports through telegram bot"

	def handle(self, *args, **options):

		now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		self.stdout.write(f"[{now}] Starting report sending...")

		send_near_reports_direct()

		now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		self.stdout.write(f"[{now}] Near reports have been sent to users.")
