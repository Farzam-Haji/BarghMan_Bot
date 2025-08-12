#django_setup--------------------------------------------------------------------#
import sys
import os
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BarghMan_Bot.settings")
django.setup()
#--------------------------------------------------------------------------------#
from django.db.models import query
from redis import commands
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes
from django.conf import settings
from accounts.models import TelegramUser
from billing.models import Bill
from blackout_checker.redis_client import store_redis_report, get_redis_report
from telegram_bot.utils import all_reports_list
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
	await update.message.reply_text("Welcome to BarghMan Bot!!!\nYou can find help with /help")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text("/add: Add a new bill to your account\n/delete: Delete one of your existing bills\n/check: get the reports for your bills")


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	if len(context.args) != 1:
		await update.message.reply_text("hint: /add <your 13 digit bill id>\nExample: /add 1234567890013")
		return
	
	bill_id = context.args[0]
	chat_id = update.effective_chat.id

	if not bill_id.isdigit() or len(bill_id) != 13:
		return await update.message.reply_text("Wrong bill number\nValid bill is 13 digit number\nExample: /add 1234567890013")
		
	if not await sync_to_async(store_redis_report)(bill_id):
		return await update.message.reply_text("We couldn't receive data for this bill")
		
	user, _ = await get_create_user(chat_id)
	await update_user_info(user, update)

	bill, _ = await get_create_bill(bill_id)
	if not await bill_exist_for_user(user, bill):
		await add_bill_to_user(user, bill)

	return await update.message.reply_text(f"bill {bill_id} was successfully added for you")


async def check_command(update: Update, conetex: ContextTypes.DEFAULT_TYPE):
	user = await get_user(update.effective_chat.id)
	bills = await all_bills_for_user(user)

	if not bills:
		return await update.message.reply_text("You have not registered any bills")
		
	bottons = [[InlineKeyboardButton(bill.bill_id, callback_data=f"check:{bill.bill_id}")]for bill in bills]
	bottons.append([InlineKeyboardButton("All", callback_data="check:all")])
	bottons.append([InlineKeyboardButton("Return", callback_data="check:return")])
	keyboard = InlineKeyboardMarkup(bottons)

	return await update.message.reply_text("Select which you bill's report you want", reply_markup=keyboard)


async def check_callback(update: Update, conetex: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	answer = query.data.split(":")[1]

	if answer == "return":
		return await query.edit_message_text(text="You canceled check process")

	await query.edit_message_text(text=f"You selected: {answer}")
	if answer == "all":
		user = await get_user(update.effective_chat.id)
		result = await sync_to_async(all_reports_list)(user)
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
		return await update.message.reply_text("You don't have any bills yet")
		

	buttons=[]
	for bill in bills:
		buttons.append([InlineKeyboardButton(bill.bill_id, callback_data=f"delete:{bill.bill_id}")])
	buttons.append([InlineKeyboardButton("Return", callback_data="delete:return")])
	keyboard = InlineKeyboardMarkup(buttons)

	return await update.message.reply_text("Select which bill you want to delete", reply_markup=keyboard)


async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
	query = update.callback_query
	await query.answer()
	answer = query.data.split(":")[1]

	if answer == "return":
		return await query.edit_message_text(text="You canceled the deletion process")
		
	user = await get_user(update.effective_chat.id)
	if await delete_bill_for_user(user, answer):
		return await query.edit_message_text(text=f"Bill <{answer}> was successfully deleted")
	else:
		return await query.edit_message_text(text="Unsuccessful. try again")





def main():
	app = ApplicationBuilder().token(bot_token).proxy(proxy_url).get_updates_proxy(proxy_url).build()

	app.add_handler(CommandHandler("start", start_command))
	app.add_handler(CommandHandler("help", help_command))
	app.add_handler(CommandHandler("add", add_command))
	app.add_handler(CommandHandler("check", check_command))
	app.add_handler(CallbackQueryHandler(check_callback, pattern="^check"))
	app.add_handler(CommandHandler("delete", delete_command))
	app.add_handler(CallbackQueryHandler(delete_callback, pattern="^delete"))
	print("bot is running")
	app.run_polling()

if __name__=="__main__":
	main()