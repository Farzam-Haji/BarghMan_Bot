import redis
import json
from django.conf import settings
from blackout_checker.utils import fetch_blackout_report, report_parser, today_tomorrow_report_parser
from billing.models import Bill
import time

def get_redis_connection():
	return redis.Redis(
			host=settings.REDIS_HOST,
			port=settings.REDIS_PORT,
			db=settings.REDIS_DB,
			decode_responses=True
		)

def store_redis_report(bill_id: str) -> Exception | None:
	r = get_redis_connection()
	key = bill_id
	try:
		value = fetch_blackout_report(bill_id)
		try:
			r.setex(key, 93600, json.dumps(value, ensure_ascii=False))
			return None
		except Exception as e:
			return e

	except Exception as e:
		return e

	


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


def update_all_bill_reports() -> Exception | None:
	bills = Bill.objects.exclude(users__isnull=True)
	for bill in bills:
		err = store_redis_report(bill.bill_id)
		if err != None:
			return err
		time.sleep(0.5)

	delete_orphan_redis_reports()