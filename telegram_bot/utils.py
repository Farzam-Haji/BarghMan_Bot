from django.conf import settings
from blackout_checker.redis_client import get_redis_report, get_redis_near_report
import requests
from accounts.models import TelegramUser
import jdatetime

def get_jalali_today():
	return jdatetime.date.today().strftime("%Y/%m/%d")


def send_telegram_message(user: TelegramUser, text: str):
	token = settings.TELEGRAM_BOT_TOKEN
	url = f"https://api.telegram.org/bot{token}/sendMessage"
	proxies = {
        "http": "http://127.0.0.1:12334",
        "https": "http://127.0.0.1:12334"
    }

	payload = {
		"chat_id": user.chat_id,
		"text": text,
		"parse_mode": "HTML"
	}

	response = requests.post(url, proxies=proxies, json=payload)
	user.msg_counter += 1
	user.save()
	return response.ok


# Manual Telegram Message Through Bot
def send_all_reports_direct() -> None:
	for user in TelegramUser.objects.filter(auto_update=True).prefetch_related("bills"):
		telegram_message = []
		for bill in user.bills.all():
			report = get_redis_report(bill.bill_id)
			if report == "":
				telegram_message.append(f"خاموشی برای قبض {bill.bill_id} گزارش نشده است.")
				continue
			bill_report = f"گزارش خاموشی برای {bill.bill_id}:\n\n" + report
			telegram_message.append(bill_report)

		send_telegram_message(user, "\n\n".join(telegram_message))

def send_near_reports_direct() -> None:
	for user in TelegramUser.objects.filter(auto_update=True).prefetch_related("bills"):
		today_message = ""
		tomorrow_message = ""

		for bill in user.bills.all():
			(today_report, tomorrow_report) = get_redis_near_report(bill.bill_id)
			today_message += today_report
			tomorrow_message += tomorrow_report

		if today_message == "" and tomorrow_message == "":
			send_telegram_message(user, "💡 خاموشی برای امروز و فردا تنظیم نشده است.")
			continue

		if today_message == "":
			today_message = "امروز:\n\nخاموشی برای امروز ثبت نشده است"
		else:
			today_message = "امروز:\n\n" + today_message
			
		if tomorrow_message == "":
			tomorrow_message = "فردا:\n\nخاموشی برای فردا ثبت نشده است"
		else:
			tomorrow_message = "فردا:\n\n" + tomorrow_message

		send_telegram_message(user, f"اخبار خاموشی برای {get_jalali_today()}\n\n" + "\n\n".join([today_message, tomorrow_message]))



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


