import requests
from django.conf import settings
from .models import Bill


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


def get_user_reports(user):
	bills = Bill.objects.filter(user=user)
	if not bills:
		return "this user has no bill"

	reports = {}
	for bill in bills:
		report = fetch_blackout_report(bill.bill_id)
		reports[bill] = report

	return reports