#django_setup--------------------------------------------------------------------#
import sys
import os
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BarghMan_Bot.settings")
django.setup()
#--------------------------------------------------------------------------------#
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from django.conf import settings
from accounts.models import TelegramUser, UserBill
from billing.models import Bill
from blackout_checker.redis_client import store_redis_report, get_redis_report
# from telegram_bot.utils import all_reports_list_bot
import asyncio
from asgiref.sync import sync_to_async
from telegram.error import NetworkError, TimedOut
from telegram.request import HTTPXRequest
import logging
import httpx



# systemd watchdog for debian\ubuntu os
# install with: sudo apt install python3-systemd
try:
	from systemd import daemon
	import threading
	import time

	def watchdog_notifier(interval:int = 10):
		"""send signal to systemd watchdog every `interval` seconds"""
		while True:
			daemon.notify("WATCHDOG=1")
			time.sleep(interval)
    
	WATCHDOG_ENABLED = True

except ImportError:
    WATCHDOG_ENABLED = False




#Bot_connection

bot_token = settings.TELEGRAM_BOT_TOKEN
proxy_url = settings.PROXY_URL

http_request = HTTPXRequest(
	connection_pool_size=20,
	pool_timeout=10.0,
	read_timeout=60.0,
	write_timeout=15.0,
	connect_timeout=10.0,
	http_version="1.1",
	proxy=proxy_url,
)


#Async_ORM

@sync_to_async
def get_user(chat_id):
	return TelegramUser.objects.get(chat_id=chat_id)

@sync_to_async
def get_create_user(chat_id):
	return TelegramUser.objects.get_or_create(chat_id=chat_id)

@sync_to_async
def get_create_bill(bill_id):
	return Bill.objects.get_or_create(bill_id=bill_id)

@sync_to_async
def add_bill_to_user(user, bill):
	return user.bills.add(bill)

@sync_to_async
def bill_exist_for_user(user, bill):
	return user.bills.filter(pk=bill.pk).exists()

@sync_to_async
def all_bills_for_user(user: TelegramUser):
	return list(user.bills.all())

@sync_to_async
def delete_bill_for_user(user: TelegramUser, bill_id: str) -> bool:
	try:
		user.bills.filter(bill_id=bill_id).delete()
		return True
	except Exception as e:
		return False

@sync_to_async
def add_msg_counter(user: TelegramUser):
	user.msg_counter += 1
	user.save()
	return

@sync_to_async
def update_user_auto_status(user: TelegramUser, status: bool):
	user.auto_update = status
	user.save()
	return

@sync_to_async
def update_user_info(user, update: Update):
	user.username = update.effective_chat.username
	user.name = update.effective_chat.full_name
	user.save()
	return

@sync_to_async
def all_alias_for_user(user: TelegramUser):
	return list(UserBill.objects.filter(user=user).select_related("bill"))

@sync_to_async
def set_new_alias(user: TelegramUser, bill_id: str, alias: str):
	userbill = UserBill.objects.get(user=user, bill__bill_id=bill_id)
	userbill.alias = alias
	userbill.save()
	return userbill

# util function for send all reports to a user
def all_reports_list_bot(user: TelegramUser) -> list:
	user_bills = user.bills.all()

	result = []
	
	if not user_bills:
		result.append("شما قبضی ثبت نکرده‌اید")
		return result

	for bill in user_bills:
		report = get_redis_report(bill.bill_id)
		if report == "":
			bill_report = f"\nگزارش خاموشی برای {bill.bill_id}:\n\n" + "خاموشی برای این قبض یافت نشد"
		else:
			bill_report = f"\nگزارش خاموشی برای {bill.bill_id}:\n\n" + report
		result.append(bill_report)

	return result



#Command_Handlers
#Start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("به ربات برق‌من خوش آمدید!\nبرای آشنایی با طریقه‌ی عملکرد ربات از /help استفاده کنید")


#Help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	return await update.message.reply_text("می‌توانید توسط یکی از دستورات زیر کار مد نظر خود را از ربات بخواهید:\n\n"
		+"/add  افزودن قبض جدید\n"
		+"/delete  حذف یکی از قبض‌های از پیش افزوده شده\n"
		+"/check  دریافت گزارش خاموشی برای قبوض افزوده شده\n"
		+"/name  تغییر نام قبض\n"
		+"/auto  دریافت اخبار خودکار\n\n"
		+"اخبار خودکار: اخبار خاموشی مربوط به امروز و فردا را به صورت روزانه دریافت میکنید.")


#Add
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	if context.args:
		return await add_validation(update, context, context.args[0])
	return	await update.message.reply_text("لطفا شماره‌ی ۱۳ رقمی قبض را وارد کنید:", reply_markup=ForceReply(selective=True))

async def add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
	bill_id = update.message.text
	chat_id = update.effective_chat.id

	#validation
	if len(bill_id) != 13 or not bill_id.isdigit():
		return  await update.message.reply_text("قبض اشتباه!\n❗قبض باید ۱۳ رقم انگلیسی باشد.\nمثال:\n1234567890013")

	#check_api_and_store_data_in_redis
	if await sync_to_async(store_redis_report)(bill_id) != None:
		return	await update.message.reply_text("موفق به دریافت اطلاعات برای این قبض نشدم. لطفا دوباره تلاش کنید.")

	#add_to_db
	user, _ = await get_create_user(chat_id)
	await update_user_info(user, update)

	bill, _ = await get_create_bill(bill_id)
	if not await bill_exist_for_user(user, bill):
		await add_bill_to_user(user, bill)

	return	await update.message.reply_text(f"قبض {bill_id} با موفقیت برای شما ثبت شد.\nمیتوانید با /check گزارش آن را دریافت کنید")


#Check
async def check_command(update: Update, conetex: ContextTypes.DEFAULT_TYPE):
	user = await get_user(update.effective_chat.id)
	bills = await all_alias_for_user(user)

	if not bills:
		return await update.message.reply_text("شما قبضی ندارید.\nابتدا با /add قبض خود را ثبت کنید")
		
	bottons = [[InlineKeyboardButton(str(bill), callback_data=f"check:{bill.bill.bill_id}:{str(bill)}")]for bill in bills]
	bottons.append([InlineKeyboardButton("همه", callback_data="check:همه:همه")])
	bottons.append([InlineKeyboardButton("بازگشت", callback_data="check:return")])
	keyboard = InlineKeyboardMarkup(bottons)

	return await update.message.reply_text("گزارش کدام قبض را می‌خواهید؟", reply_markup=keyboard)


async def check_callback(update: Update, conetex: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	answer = query.data.split(":")[1]
	alias = query.data.split(":")[2]
	

	if answer == "return":
		return await query.edit_message_text(text="شما پروسه‌ی دریافت خاموشی را متوقف کردید")

	await query.edit_message_text(text=f"انتخاب شما: {alias}")
	user = await get_user(update.effective_chat.id)
	if answer == "همه":
		result = await sync_to_async(all_reports_list_bot)(user)
		for bill_report in result:
			await query.message.reply_text(bill_report)
			await add_msg_counter(user)
			await asyncio.sleep(0.1)
		return

	single_bill_report = await sync_to_async(get_redis_report)(answer)
	if single_bill_report == "":
		await query.message.reply_text("خاموشی برای این قبض یافت نشد.")
		return await add_msg_counter(user)
	await query.message.reply_text(single_bill_report)
	return await add_msg_counter(user)


#Delete
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user = await get_user(update.effective_chat.id)
	bills = await all_bills_for_user(user)

	if not bills:
		return await update.message.reply_text("شما قبضی ندارید")
		

	buttons=[]
	for bill in bills:
		buttons.append([InlineKeyboardButton(bill.bill_id, callback_data=f"delete:{bill.bill_id}")])
	buttons.append([InlineKeyboardButton("بازگشت", callback_data="delete:return")])
	keyboard = InlineKeyboardMarkup(buttons)

	return await update.message.reply_text("کدام قبض را میخواهید حذف کنید؟", reply_markup=keyboard)


async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	answer = query.data.split(":")[1]

	if answer == "return":
		return await query.edit_message_text(text="شما پروسه‌ی حذف قبض را متوقف کردید")
		
	user = await get_user(update.effective_chat.id)
	if await delete_bill_for_user(user, answer):
		return await query.edit_message_text(text=f"قبض {answer} با موفقیت حذف شد")
	else:
		return await query.edit_message_text(text="ناموفق. لطفا دوباره تلاش کنید")



#Auto
async def auto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user = await get_user(update.effective_chat.id)
	current = ""
	if user.auto_update:
		current = "فعال"
	else:
		current = "غیرفعال"

	buttons = [
		[
			InlineKeyboardButton("فعال", callback_data="auto:active"),
			InlineKeyboardButton("غیرفعال", callback_data="auto:inactive")
		]
	]

	keyboard = InlineKeyboardMarkup(buttons)
	return await update.message.reply_text(f"وضعیت فعلی دریافت خودکار اخبار: {current}", reply_markup=keyboard)


async def auto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	answer = query.data.split(":")[1]
	user = await get_user(update.effective_chat.id)

	if answer == "active":
		await update_user_auto_status(user, True)
		return	await query.edit_message_text(text="اخبار خودکار فعال شد.")

	if answer == "inactive":
		await update_user_auto_status(user, False)
		return	await query.edit_message_text(text="اخبار خودکار غیرفعال شد.")



#Name
async def name_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user = await get_user(update.effective_chat.id)
	bills = await all_alias_for_user(user)

	if not bills:
		return await update.message.reply_text("شما قبضی ندارید.\nابتدا با /add قبض خود را ثبت کنید")
		
	bottons = [[InlineKeyboardButton(str(bill), callback_data=f"name:{bill.bill.bill_id}")]for bill in bills]
	bottons.append([InlineKeyboardButton("بازگشت", callback_data="name:return")])
	keyboard = InlineKeyboardMarkup(bottons)

	return await update.message.reply_text("نام کدام قبض را می‌خواهید تغییر دهید؟", reply_markup=keyboard)

async def name_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	answer = query.data.split(":")[1]

	if answer == "return":
		return await query.edit_message_text(text="شما پروسه‌ی تغییر نام را متوقف کردید")
		
	context.user_data["rename_bill_id"] = answer
	
	await query.edit_message_text(text=f"لطفا نام جدید برای قبض {answer} را وارد کنید.\n"
		+"میتوانید با وارد کردن 0 نام قبض را حذف کنید")
	return await query.message.reply_text("نام جدید:", reply_markup=ForceReply(selective=True))


async def name_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
	bill_id = context.user_data.get("rename_bill_id")
	user = await get_user(update.effective_chat.id)
	alias = update.message.text

	if alias == "0" or alias == "۰":
		await set_new_alias(user, bill_id, "")
		return await update.message.reply_text(f"نام قبض {bill_id} حذف شد.")

	await set_new_alias(user, bill_id, alias)

	return await update.message.reply_text(f"نام قبض {bill_id} با موفقیت به {alias} تغییر یافت")




#Reply text
async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    text = update.message.reply_to_message.text

    if "۱۳ رقمی قبض" in text:
        return await add_reply(update, context)

    if "نام جدید:" in text:
        return await name_reply(update, context)



#Log_and_Errors

logger = logging.getLogger(__name__)
logging.basicConfig(
	format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
	level=logging.INFO,
)


async def error_handler(update, context):
	error = context.error

	cause = getattr(error, "__cause__", None)

	if isinstance(error, httpx.ConnectError) or isinstance(cause, httpx.ConnectError):
		logger.error("Proxy connection failed. Exiting so systemd can restart.")
		sys.exit(1)

	elif isinstance(error, (NetworkError, httpx.RemoteProtocolError)):
		logger.warning("Network issue: %s", error)
	
	else:
		logger.error("Unexpected error: %s", error, exc_info=error)


def main():
	app = ApplicationBuilder().token(bot_token).request(http_request).get_updates_request(http_request).build()

	#handlers
	app.add_handler(CommandHandler("start", start_command))
	app.add_handler(CommandHandler("help", help_command))
	app.add_handler(CommandHandler("add", add_command))
	app.add_handler(CommandHandler("check", check_command))
	app.add_handler(CallbackQueryHandler(check_callback, pattern="^check"))
	app.add_handler(CommandHandler("delete", delete_command))
	app.add_handler(CallbackQueryHandler(delete_callback, pattern="^delete"))
	app.add_handler(CommandHandler('auto', auto_command))
	app.add_handler(CallbackQueryHandler(auto_callback, pattern="^auto"))
	app.add_handler(CommandHandler("name", name_command))
	app.add_handler(CallbackQueryHandler(name_callback, pattern="^name"))
	#handler for reply messages
	app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, reply_handler))

	#error_handler
	app.add_error_handler(error_handler)

	#watchdog
	if WATCHDOG_ENABLED:
		threading.Thread(target=watchdog_notifier, daemon=True).start()

	logger.info("Bot is running")
	app.run_polling(
		drop_pending_updates=True,
		allowed_updates=["message", "callback_query"],
		timeout=10,
		stop_signals=None,
		close_loop=False,
		poll_interval=5.0,
	)



if __name__=="__main__":
	if WATCHDOG_ENABLED:
		daemon.notify("READY=1")
	main()