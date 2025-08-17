from django.core.management.base import BaseCommand
from accounts.utils import get_total_user, get_total_report_sent
from datetime import datetime

class Command(BaseCommand):
	help = "Get the total number of users with at least one bill, and the total number of outage reports sent by the Telegram bot."

	def handle(self, *args, **options):
		now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
		total_user = get_total_user()
		total_message = get_total_report_sent()
		self.stdout.write(
			f"At [{now}], there are {total_user} active users, and a total of {total_message} reports have been sent."
		)
		