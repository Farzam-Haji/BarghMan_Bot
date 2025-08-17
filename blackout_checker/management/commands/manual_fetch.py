from django.core.management.base import BaseCommand
from blackout_checker.utils import fetch_blackout_report, report_parser


class Command(BaseCommand):
	help = "Fetch the report of a given bill from API"

	def handle(self, *args, **options):
		self.stdout.write("Please enter the bill ID => ", ending="")
		bill_id = input()
		try:
			report = report_parser(fetch_blackout_report(bill_id))
			self.stdout.write(report)
		except Exception as e:
			self.stderr.write(f"Error occured: {e}")