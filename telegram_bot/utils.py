from django.conf import settings
from billing.utils import get_user_reports
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
	reports = get_user_reports(user)

	for bill, report in reports.items():
		text = f"report for {bill}: {report}"
		send_telegram_message(user.chat_id, text)