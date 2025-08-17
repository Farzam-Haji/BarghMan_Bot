from django.db.models import Sum
from .models import TelegramUser



def get_total_user():
	total_user = TelegramUser.objects.filter(bills__isnull=False).distinct().count()
	return total_user

def get_total_report_sent():
	total_msg = TelegramUser.objects.aggregate(Sum("msg_counter"))["msg_counter__sum"] or 0
	return total_msg