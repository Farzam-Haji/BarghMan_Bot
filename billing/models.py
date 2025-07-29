from django.db import models
from django.conf import settings

from accounts.models import TelegramUser

# Create your models here.
class Bill(models.Model):
	user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
	location = models.CharField(max_length=200)
	bill_id = models.CharField(max_length=13, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.location}({self.bill_id})"