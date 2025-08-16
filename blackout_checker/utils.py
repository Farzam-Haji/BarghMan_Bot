import datetime
import requests
import json
from django.conf import settings
from billing.models import Bill
import jdatetime
from datetime import date



def jalali_to_gregorian(persian_date: str) -> date:
	return jdatetime.date.fromisoformat(persian_date.replace("/", "-")).togregorian()



def sort_date_key(report):
	return jalali_to_gregorian(report.get('outage_date'))



def fetch_blackout_report(bill_id:str):
	API_TOKEN = f"Bearer {settings.BLACKOUT_API_TOKEN}"
	API_URL = "https://uiapi2.saapa.ir/api/ebills/PlannedBlackoutsReport"
	headers = {
		"accept": "application/json, text/plain, */*",
		"authorization": API_TOKEN,
		"content-type": "application/json; charset=UTF-8",
	}
	payload = {
		"bill_id": bill_id,
		"from_date": "1404/05/05",
		"to_date": "1410/05/05"
	}
	response = requests.post(API_URL, headers=headers, json=payload)

	response.raise_for_status()
	return response.json()


def report_parser(json) -> str:
	data = json['data']
	data.sort(key=sort_date_key)
	parsed_reports = []

	for report in data:
		date = report.get('outage_date')
		start_time = report.get('outage_start_time')
		end_time = report.get('outage_stop_time')
		location = report.get('address')

		text = f"🌆  منطقه: {location}\n📅  تاریخ: {date}\n⏰  از: {start_time}  |  تا: {end_time}"
		parsed_reports.append(text)

	return "\n\n".join(parsed_reports)


def today_tomorrow_report_parser(json) -> tuple:
	data = json['data']
	today_reports = []
	tomorrow_report = []

	today = datetime.date.today()

	for report in data:
		gap = (jalali_to_gregorian(report.get('outage_date')) - today).days
		if gap == 0:
			start_time = report.get('outage_start_time')
			end_time = report.get('outage_stop_time')
			location = report.get('address')

			text = f"🌆  منطقه: {location}\n⏰  از: {start_time}  |  تا: {end_time}"
			today_reports.append(text)
		if gap == 1:
			start_time = report.get('outage_start_time')
			end_time = report.get('outage_stop_time')
			location = report.get('address')

			text = f"🌆  منطقه: {location}\n⏰  از: {start_time}  |  تا: {end_time}"
			tomorrow_report.append(text)

	if len(today_reports) == 0 and len(tomorrow_report) == 0:
		return "💡 خاموشی برای امروز و فردا تنظیم نشده است."

	today_str = ""
	if len(today_reports) > 0:
		today_str = "\n\n".join(today_reports)

	tomorrow_str = ""
	if len(tomorrow_report) > 0:
		today_str = "\n\n".join(tomorrow_report)

	return (today_str, tomorrow_str)




# def get_user_reports(user):
# 	user_bills = user.bills
# 	if not user_bills:
# 		return "this user has no bill"

# 	reports = []
# 	for bill in user_bills:
# 		for report in get_redis_report(bill.bill_id):
# 			reports.append(report)

# 	return reports