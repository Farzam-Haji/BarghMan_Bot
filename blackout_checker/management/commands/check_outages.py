from django.core.management.base import BaseCommand
from blackout_checker.redis_client import update_all_bill_reports
from datetime import datetime


class Command(BaseCommand):
	help = "Fetch new blackout reports from the api and update Redis"

	def handle(self, *args, **options):
		err = update_all_bill_reports()
		now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
		if err == None :
			self.stdout.write(f"[{now}] Redis reports updated")
		else:
			now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
			self.stderr.write(f"[{now}] Error while updating redis reports: {err}")	
