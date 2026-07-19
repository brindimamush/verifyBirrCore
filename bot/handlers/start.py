from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from api import check_merchant_status
from keyboards import main_menu_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and main menu."""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    # Check if already registered
    is_registered = await check_merchant_status(user.id)
    context.user_data["is_registered"] = is_registered
    
    if is_registered:
        await update.message.reply_text(
            f"Welcome back, {user.first_name}! 👋\n\n"
            "You're already registered as a merchant.\n\n"
            "Available commands:\n"
            "/subscribe - Manage your subscription\n"
            "/status - Check your account status",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(
            f"Welcome, {user.first_name}! 👋\n\n"
            "I can help you register as a merchant and manage your subscription.\n\n"
            "To get started, use /register to sign up.",
        )