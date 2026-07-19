from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    PicklePersistence,
)
from config import BOT_TOKEN
from handlers.start import start
from handlers.register import (
    register_start,
    business_name,
    business_email,
    phone,
    telebirr_name,
    telebirr_number,
    confirm_callback,
)
from handlers.subscribe import subscribe_start, plan_selected, subscribe_cancel
from states import RegistrationState

async def status_command(update, context):
    """Check registration and subscription status."""
    from api import check_merchant_status
    user = update.effective_user
    
    is_registered = await check_merchant_status(user.id)
    context.user_data["is_registered"] = is_registered
    
    if is_registered:
        await update.message.reply_text(
            "✅ You are registered as a merchant.\n\n"
            "Use /subscribe to manage your subscription plan."
        )
    else:
        await update.message.reply_text(
            "❌ You are not registered yet.\n\n"
            "Use /register to sign up as a merchant."
        )

async def cancel_command(update, context):
    """Cancel current operation."""
    await update.message.reply_text(
        "Operation cancelled. Use /start to see available commands."
    )
    return ConversationHandler.END

def build_app() -> Application:
    persistence = PicklePersistence(filepath="bot_data.pickle")
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    reg_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            RegistrationState.BUSINESS_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, business_name)
            ],
            RegistrationState.BUSINESS_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, business_email)
            ],
            RegistrationState.PHONE: [
                MessageHandler(filters.CONTACT, phone)
            ],
            RegistrationState.TELEBIRR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, telebirr_name)
            ],
            RegistrationState.TELEBIRR_NUMBER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, telebirr_number)
            ],
            RegistrationState.CONFIRM: [
                CallbackQueryHandler(confirm_callback, pattern="^(reg_confirm|reg_cancel)$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        persistent=True,
        name="registration",
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(reg_handler)
    app.add_handler(CommandHandler("subscribe", subscribe_start))
    app.add_handler(CallbackQueryHandler(plan_selected, pattern=r"^sub_plan_\d+$"))
    app.add_handler(CallbackQueryHandler(subscribe_cancel, pattern="^sub_cancel$"))

    return app