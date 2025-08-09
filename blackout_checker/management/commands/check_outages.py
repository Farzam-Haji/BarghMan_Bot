from django.core.management.base import BaseCommand
from blackout_checker.redis_client import update_all_bill_reports


class Command(BaseCommand):
	help = "Fetch new blackout reports from the api and update Redis"

	def handle(self, *args, **options):
		update_all_bill_reports()
		self.stdout.write("Redis reports updated")