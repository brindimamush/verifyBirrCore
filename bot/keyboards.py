from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Share phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def get_confirm_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes, register me", callback_data="reg_confirm"),
            InlineKeyboardButton("❌ No, start over", callback_data="reg_cancel"),
        ]
    ])

def remove_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("…")]], resize_keyboard=True, one_time_keyboard=True)

def get_plans_keyboard(plans: list[dict]):
    buttons = [
        [InlineKeyboardButton(f"{p['name']} – {p['price']} ETB", callback_data=f"sub_plan_{p['id']}")]
        for p in plans
    ]
    buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="sub_cancel")])
    return InlineKeyboardMarkup(buttons)

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        [["📊 Dashboard", "💰 Subscribe"], ["⚙️ Settings"]],
        resize_keyboard=True,
    )