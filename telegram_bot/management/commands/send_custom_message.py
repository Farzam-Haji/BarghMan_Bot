from django.core.management.base import BaseCommand
from telegram_bot.utils import custom_msg_to_alluser
from datetime import datetime


class Command(BaseCommand):
	help = "send a custom bot message to every user"

	def handle(self, *args, **options):
		self.stdout.write("Please write the global message you want to send => ", ending="")
		message = input()

		now = datetime.now().strftime("%H:%M:%S")
		self.stdout.write(f"[{now}] Begin sending...")

		res = custom_msg_to_alluser(message)
		if res != None:
			self.stderr.write("These errors accrued:", ending="")
			for user, err in res:
				self.stdout.write(f"{user}: {err}")

		now = datetime.now().strftime("%H:%M:%S")
		self.stdout.write(f"[{now}] Done")