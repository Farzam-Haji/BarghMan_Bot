#django_setup--------------------------------------------------------------------#
import sys
import os
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BarghMan_Bot.settings")
django.setup()
#--------------------------------------------------------------------------------#
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update, ForceReply
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from django.conf import settings
from accounts.models import TelegramUser
from billing.models import Bill
from blackout_checker.redis_client import store_redis_report, get_redis_report
from telegram_bot.utils import all_reports_list_bot
import asyncio
from asgiref.sync import sync_to_async


#Bot_connection

bot_token = settings.TELEGRAM_BOT_TOKEN
proxy_url = "http://127.0.0.1:12334"



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
def delete_bill_for_user(user:TelegramUser, bill_id: str) -> bool:
	try:
		user.bills.filter(bill_id=bill_id).delete()
		return True
	except Exception as e:
		return False

@sync_to_async
def update_user_info(user, update: Update):
	user.username = update.effective_chat.username
	user.name = update.effective_chat.full_name
	user.save()



#Command_Handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("به ربات برق‌من خوش آمدید!\nبرای آشنایی با طریقه‌ی عملکرد ربات از /help استفاده کنید")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	return await update.message.reply_text("می‌توانید توسط یکی از دستورات زیر کار مد نظر خود را از ربات بخواهید:\n\n"
		+"/add  افزودن قبض جدید\n"
		+"/delete  حذف یکی از قبض‌های از پیش افزوده شده\n"
		+"/check  دریافت گزارش خاموشی برای قبوض افزوده شده")


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	if context.args:
		return await add_validation(update, context, context.args[0])
	return	await update.message.reply_text("لطفا شماره‌ی ۱۳ رقمی قبض را وارد کنید:", reply_markup=ForceReply(selective=True))

async def add_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
	#check_if_it_is_a_related_message
	if not update.message.reply_to_message or "۱۳ رقمی قبض" not in update.message.reply_to_message.text:
		return

	bill_id = update.message.text
	return	await add_validation(update, context, bill_id)

async def add_validation(update: Update, context: ContextTypes.DEFAULT_TYPE, bill_id):
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


async def check_command(update: Update, conetex: ContextTypes.DEFAULT_TYPE):
	user = await get_user(update.effective_chat.id)
	bills = await all_bills_for_user(user)

	if not bills:
		return await update.message.reply_text("شما قبضی ندارید.\nابتدا با /add قبض خود را ثبت کنید")
		
	bottons = [[InlineKeyboardButton(bill.bill_id, callback_data=f"check:{bill.bill_id}")]for bill in bills]
	bottons.append([InlineKeyboardButton("همه", callback_data="check:همه")])
	bottons.append([InlineKeyboardButton("بازگشت", callback_data="check:return")])
	keyboard = InlineKeyboardMarkup(bottons)

	return await update.message.reply_text("گزارش کدام قبض را می‌خواهید؟", reply_markup=keyboard)


async def check_callback(update: Update, conetex: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	answer = query.data.split(":")[1]

	if answer == "return":
		return await query.edit_message_text(text="شما پروسه‌ی دریافت خاموشی را متوقف کردید")

	await query.edit_message_text(text=f"انتخاب شما: {answer}")
	if answer == "همه":
		user = await get_user(update.effective_chat.id)
		result = await sync_to_async(all_reports_list_bot)(user)
		for bill_report in result:
			await query.message.reply_text(bill_report)
			await asyncio.sleep(0.1)
		return

	single_bill_report = await sync_to_async(get_redis_report)(answer)
	return await query.message.reply_text(single_bill_report)


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user = await get_user(update.effective_chat.id)
	bills = await all_bills_for_user(user)

	if not bills:
		return await update.message.reply_text("شما قبضی ندارید")
		

	buttons=[]
	for bill in bills:
		buttons.append([InlineKeyboardButton(bill.bill_id, callback_data=f"delete:{bill.bill_id}")])
	buttons.append([InlineKeyboardButton("Return", callback_data="delete:return")])
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





def main():
	app = ApplicationBuilder().token(bot_token).proxy(proxy_url).get_updates_proxy(proxy_url).build()

	app.add_handler(CommandHandler("start", start_command))
	app.add_handler(CommandHandler("help", help_command))
	app.add_handler(CommandHandler("add", add_command))
	app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, add_reply))
	app.add_handler(CommandHandler("check", check_command))
	app.add_handler(CallbackQueryHandler(check_callback, pattern="^check"))
	app.add_handler(CommandHandler("delete", delete_command))
	app.add_handler(CallbackQueryHandler(delete_callback, pattern="^delete"))
	print("bot is running")
	app.run_polling()

if __name__=="__main__":
	main()