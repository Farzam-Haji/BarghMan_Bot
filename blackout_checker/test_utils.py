# this a production testing file

import django
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BarghMan_Bot.settings")
django.setup()



from blackout_checker.utils import fetch_blackout_report

bill_id = "9136846104129"
result = fetch_blackout_report(bill_id)
print(result)



# from blackout_checker.utils import get_user_reports
# from accounts.models import TelegramUser

# user = TelegramUser.objects.filter(username="@Oceanus_95").first()
# # print(user)
# reps=get_user_reports(user)
# for bill, rep in reps.items():
# 	for parsRep in rep:
# 		print(parsRep)