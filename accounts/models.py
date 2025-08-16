from django.db import models

# Create your models here.
class TelegramUser(models.Model):
	chat_id = models.BigIntegerField(unique=True)
	username = models.CharField(max_length=100, blank=True, null=True)
	name = models.CharField(max_length=100, blank=True, null=True)
	bills = models.ManyToManyField("billing.Bill", related_name="users", blank=True)
	auto_update = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.username or f"User {self.chat_id}"