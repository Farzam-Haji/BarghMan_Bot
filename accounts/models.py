from django.db import models

# Create your models here.
class TelegramUser(models.Model):
	chat_id = models.BigIntegerField(unique=True)
	username = models.CharField(max_length=100, blank=True, null=True)
	name = models.CharField(max_length=100, blank=True, null=True)
	bills = models.ManyToManyField("billing.Bill", through="UserBill", related_name="users", blank=True)
	auto_update = models.BooleanField(default=True)
	msg_counter = models.BigIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.username or f"User {self.chat_id}"


class UserBill(models.Model):
	user = models.ForeignKey("accounts.TelegramUser", on_delete=models.CASCADE)
	bill = models.ForeignKey("billing.Bill", on_delete=models.CASCADE)
	alias = models.CharField(max_length=100, blank=True, default="")

	class Meta:
		constraints = [
		models.UniqueConstraint(fields=["user", "bill"], name="unique_user_bill"),
		models.UniqueConstraint(fields=["user", "alias"], name="unique_user_alias"),
		]

	def __str__(self):
		return self.alias or self.bill.bill_id