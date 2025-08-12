from django.conf import settings
from blackout_checker.redis_client import get_redis_report
import requests
from accounts.models import TelegramUser


def send_telegram_message(chat_id, text):
	token = settings.TELEGRAM_BOT_TOKEN
	url = f"https://api.telegram.org/bot{token}/sendMessage"
	proxies = {
        "http": "http://127.0.0.1:12334",
        "https": "http://127.0.0.1:12334"
    }

	payload = {
		"chat_id": chat_id,
		"text": text,
		"parse_mode": "HTML"
	}

	response = requests.post(url, proxies=proxies, json=payload)
	return response.ok

# send reports to all the users
def send_telegram_user_reports():
	all_users = TelegramUser.objects.all()
	for user in all_users:
		user_bills = user.bills.all()
		if not user_bills:
			continue
		for bill in user_bills:
			bill_report = f"report for {bill.bill_id}:\n\n" + get_redis_report(bill.bill_id)
			send_telegram_message(user.chat_id, get_redis_report(bill.bill_id))


def all_reports_list(user: TelegramUser):
	user_bills = user.bills.all()

	result = []
	
	if not user_bills:
		result.append("You have no bills")
		return result

	for bill in user_bills:
		bill_report = f"report for {bill.bill_id}:\n\n" + get_redis_report(bill.bill_id)
		result.append(bill_report)

	return result