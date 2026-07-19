from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from keyboards import get_plans_keyboard, main_menu_keyboard
from api import get_plans, subscribe, SubscriptionError, check_merchant_status

async def subscribe_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available plans, but only if registered."""
    user = update.effective_user
    
    # Check registration status
    is_registered = context.user_data.get("is_registered", False)
    if not is_registered:
        # Double-check with backend
        is_registered = await check_merchant_status(user.id)
        context.user_data["is_registered"] = is_registered
    
    if not is_registered:
        await update.message.reply_text(
            "❌ You need to register as a merchant first!\n\n"
            "Please use /register to sign up, then you can subscribe to a plan.",
        )
        return
    
    # Fetch and display plans
    plans = await get_plans()
    if not plans:
        await update.message.reply_text("No subscription plans available at the moment.")
        return

    await update.message.reply_text(
        "Choose a plan:",
        reply_markup=get_plans_keyboard(plans),
    )

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plan_id = int(query.data.split("_")[-1])
    telegram_id = update.effective_user.id

    await query.edit_message_text("⏳ Processing your subscription...")

    try:
        result = await subscribe(telegram_id=telegram_id, plan_id=plan_id)
        verification_url = result.get("verification_url")
        token = result.get("token")
        msg = (
            "📬 **Subscription created!**\n\n"
            f"Please complete payment using the link below:\n{verification_url}\n\n"
            f"Your payment token: `{token}`\n\n"
            "After payment is confirmed, your subscription will be activated automatically."
        )
        await query.message.reply_text(msg, parse_mode="Markdown")
        logger.info(f"User {telegram_id} subscribed to plan {plan_id}")
    except SubscriptionError as e:
        await query.message.reply_text(f"❌ Subscription failed: {e}")
    except Exception as e:
        await query.message.reply_text("❌ A system error occurred. Please try again later.")
        logger.exception(f"Subscription error for user {telegram_id}")

    await query.message.reply_text(
        "What would you like to do next?",
        reply_markup=main_menu_keyboard()
    )

async def subscribe_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Subscription cancelled.")
    await query.message.reply_text(
        "Use /subscribe anytime to choose a plan.",
        reply_markup=main_menu_keyboard()
    )