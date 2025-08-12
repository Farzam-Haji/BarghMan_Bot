import requests
import json
from django.conf import settings
from billing.models import Bill


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

def report_parser(json):
	data = json['data']
	parsed_reports = []

	for report in data:
		date = report.get('outage_date')
		start_time = report.get('outage_start_time')
		end_time = report.get('outage_stop_time')
		location = report.get('address')

		text = f"{location}\ndate: {date} | from: {start_time} | to: {end_time}"
		parsed_reports.append(text)

	return "\n\n".join(parsed_reports)


# def get_user_reports(user):
# 	user_bills = user.bills
# 	if not user_bills:
# 		return "this user has no bill"

# 	reports = []
# 	for bill in user_bills:
# 		for report in get_redis_report(bill.bill_id):
# 			reports.append(report)

# 	return reports