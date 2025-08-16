from django.conf import settings
from blackout_checker.redis_client import get_redis_report, get_redis_near_report
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


# Manual Telegram Message Through Bot
def send_all_reports_direct() -> None:
	all_users = TelegramUser.objects.all()
	for user in all_users:
		user_bills = user.bills.all()
		if not user_bills:
			continue

		telegram_message = []
		for bill in user_bills:
			bill_report = f"گزارش خاموشی برای {bill.bill_id}:\n\n" + get_redis_report(bill.bill_id)
			telegram_message.append(bill_report)
			
		send_telegram_message(user.chat_id, "\n\n".join(telegram_message))

def send_near_reports_direct() -> None:
	all_users = TelegramUser.objects.all()
	for user in all_users:
		user_bills = user.bills.all()
		if not user_bills:
			continue
		
		today_message = ""
		tomorrow_message = ""
		for bill in user_bills:
			(today_report, tomorrow_report) = get_redis_near_report(bill.bill_id)
			today_message += today_report
			tomorrow_message += tomorrow_report

		if today_message != "":
			today_message = "امروز:\n\n" + today_message
		if tomorrow_message != "":
			tomorrow_message = "\n\nفردا:\n\n" + tomorrow_message

		send_telegram_message(user.chat_id, "\n\n".join([today_message, tomorrow_message]))



# Telegram Bot
def all_reports_list_bot(user: TelegramUser) -> list:
	user_bills = user.bills.all()

	result = []
	
	if not user_bills:
		result.append("شما قبضی ثبت نکرده‌اید")
		return result

	for bill in user_bills:
		bill_report = f"\nگزارش خاموشی برای {bill.bill_id}:\n\n" + get_redis_report(bill.bill_id)
		result.append(bill_report)

	return result


