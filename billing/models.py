from django.db import models

# Create your models here.
class Bill(models.Model):
	bill_id = models.CharField(max_length=13, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.bill_id}"
