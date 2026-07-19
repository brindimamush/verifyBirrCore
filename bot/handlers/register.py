import re
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from states import RegistrationState
from keyboards import get_phone_keyboard, get_confirm_keyboard, remove_keyboard, main_menu_keyboard
from api import register_merchant, RegistrationError, check_merchant_status

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration conversation with pre-check."""
    user = update.effective_user
    
    # Check if already registered
    is_registered = await check_merchant_status(user.id)
    
    if is_registered:
        await update.message.reply_text(
            "✅ You are already registered as a merchant!\n\n"
            "Available commands:\n"
            "/subscribe - Manage your subscription\n"
            "/status - Check your account status",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END
    
    # Clear any previous data
    context.user_data.clear()
    await update.message.reply_text(
        "Let's register you as a merchant! 🚀\n\n"
        "First, what is your **business name**?\n\n"
        "Send /cancel at any time to abort registration.",
    )
    return RegistrationState.BUSINESS_NAME

async def business_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Business name must be at least 2 characters. Please try again:")
        return RegistrationState.BUSINESS_NAME
    context.user_data["business_name"] = name
    await update.message.reply_text("Great! What is your **business email**?")
    return RegistrationState.BUSINESS_EMAIL

async def business_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text("Please enter a valid email address:")
        return RegistrationState.BUSINESS_EMAIL
    context.user_data["business_email"] = email
    await update.message.reply_text(
        "Now, please share your **phone number** using the button below.",
        reply_markup=get_phone_keyboard(),
    )
    return RegistrationState.PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Please use the 'Share phone number' button.")
        return RegistrationState.PHONE

    phone_number = contact.phone_number.replace(" ", "").lstrip("+")
    if not phone_number.startswith("251"):
        await update.message.reply_text(
            "The phone number must be an Ethiopian number (+251...). Try again with the button."
        )
        return RegistrationState.PHONE

    # Convert to 09xxxxxxxx format
    if phone_number.startswith("251"):
        phone_number = "0" + phone_number[3:]
    if not re.match(r"^09\d{8}$", phone_number):
        await update.message.reply_text(
            "The phone number doesn't look right. It must be 10 digits starting with 09.\n"
            "Please share your contact again."
        )
        return RegistrationState.PHONE

    context.user_data["phone_number"] = phone_number
    await update.message.reply_text("Phone number saved! 👍", reply_markup=remove_keyboard())
    await update.message.reply_text(
        "What is your **Telebirr name**? (The exact name as it appears in your Telebirr app)"
    )
    return RegistrationState.TELEBIRR_NAME

async def telebirr_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("Name must be at least 2 characters. Please enter again:")
        return RegistrationState.TELEBIRR_NAME
    context.user_data["telebirr_name"] = name
    await update.message.reply_text(
        "What is your **Telebirr number**?\n"
        "It must be 10 digits starting with 09 (e.g. 0912345678)."
    )
    return RegistrationState.TELEBIRR_NUMBER

async def telebirr_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    number = update.message.text.strip().replace(" ", "")
    if not re.match(r"^09\d{8}$", number):
        await update.message.reply_text(
            "Invalid format. Telebirr number must be exactly 10 digits starting with 09.\n"
            "Try again:"
        )
        return RegistrationState.TELEBIRR_NUMBER
    context.user_data["telebirr_number"] = number

    summary = (
        "📋 **Registration Summary**\n\n"
        f"• Business: {context.user_data['business_name']}\n"
        f"• Email: {context.user_data['business_email']}\n"
        f"• Phone: {context.user_data['phone_number']}\n"
        f"• Telebirr Name: {context.user_data['telebirr_name']}\n"
        f"• Telebirr No.: {context.user_data['telebirr_number']}\n\n"
        "Is this correct?"
    )
    await update.message.reply_text(summary, reply_markup=get_confirm_keyboard())
    return RegistrationState.CONFIRM

async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "reg_cancel":
        await query.edit_message_text("Registration cancelled. Use /register to start again.")
        context.user_data.clear()
        return ConversationHandler.END

    await query.edit_message_text("🔄 Registering you with our system, please wait...")
    try:
        result = await register_merchant(
            telegram_id=update.effective_user.id,
            phone_number=context.user_data["phone_number"],
            business_name=context.user_data["business_name"],
            business_email=context.user_data["business_email"],
            telebirr_name=context.user_data["telebirr_name"],
            telebirr_number=context.user_data["telebirr_number"],
        )
        context.user_data["merchant_id"] = result.get("merchant_id")
        context.user_data["is_registered"] = True
        
        await query.message.reply_text(
            "✅ **Registration successful!** You are now a registered merchant.\n\n"
            "What would you like to do next?\n"
            "/subscribe - Choose a subscription plan\n"
            "/status - Check your account status",
            reply_markup=main_menu_keyboard(),
        )
        logger.info(f"User {update.effective_user.id} registered as merchant {context.user_data.get('merchant_id')}")
    except RegistrationError as e:
        await query.message.reply_text(f"❌ Registration failed: {e}\n\nPlease try again with /register")
        logger.error(f"Registration error for user {update.effective_user.id}: {e}")
    except Exception as e:
        await query.message.reply_text("❌ A system error occurred. Please try again later or contact support.")
        logger.exception(f"Unexpected registration error for user {update.effective_user.id}")
    finally:
        # Don't clear merchant_id and is_registered
        merchant_id = context.user_data.pop("merchant_id", None)
        is_registered = context.user_data.pop("is_registered", None)
        context.user_data.clear()
        if merchant_id:
            context.user_data["merchant_id"] = merchant_id
        if is_registered:
            context.user_data["is_registered"] = is_registered
            
    return ConversationHandler.END