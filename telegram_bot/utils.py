from django.conf import settings
from blackout_checker.redis_client import get_redis_report
import requests

def send_telegram_message(chat_id, text):
	token = settings.TELEGRAM_BOT_TOKEN
	url = f"https://api.telegram.org/bot{token}/sendMessage"

	payload = {
		"chat_id": chat_id,
		"text": text,
		"parse_mode": "HTML"
	}

	response = requests.post(url, json=payload)
	return response.ok


def send_telegram_user_reports(user):
	user_bills = user.bills.all()

	if not user_bills:
		return ("This user has no bill")

	for bill in user_bills:
		for report in get_redis_report(bill.bill_id):
			send_telegram_message(user.chat_id, report)