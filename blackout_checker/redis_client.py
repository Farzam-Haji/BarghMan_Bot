import redis
import json
from django.conf import settings
from blackout_checker.utils import fetch_blackout_report, report_parser, today_tomorrow_report_parser
from billing.models import Bill

def get_redis_connection():
	return redis.Redis(
			host=settings.REDIS_HOST,
			port=settings.REDIS_PORT,
			db=settings.REDIS_DB,
			decode_responses=True
		)

def store_redis_report(bill_id: str) -> bool:
	r = get_redis_connection()
	key = bill_id
	try:
		value = fetch_blackout_report(bill_id)
	except Exception as e:
		print(f"Error during fetching data from api: {e}")
		return False

	try:
		r.setex(key, 93600, json.dumps(value, ensure_ascii=False))
		return True
	except Exception as e:
		print("Error with redis: {e}")
		return False


def get_redis_report(bill_id: str) -> str:
	r = get_redis_connection()
	json_report = r.get(bill_id)
	if json_report is None:
		return ""
	else:
		return report_parser(json.loads(json_report))


def get_redis_near_report(bill_id: str) -> str:
	r = get_redis_connection()
	json_report = r.get(bill_id)
	if json_report is None:
		return ""
	else:
		return today_tomorrow_report_parser(json.loads(json_report))


def delete_orphan_redis_reports():
	orphan_bills = Bill.objects.filter(users__isnull=True)
	r = get_redis_connection()
	for bill in orphan_bills:
		r.delete(bill.bill_id)


def update_all_bill_reports():
	bills = Bill.objects.exclude(users__isnull=True)
	for bill in bills:
		store_redis_report(bill.bill_id)

	delete_orphan_redis_reports()