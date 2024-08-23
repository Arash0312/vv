from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import csv
import os
import requests
from requests.adapters import HTTPAdapter, Retry

# دریافت توکن از متغیر محیطی
TOKEN = '7291961799:AAFN8zhDY_2_TY5NMYEbuJ1P6hAzU7xnr3Q'
# آدرس API تلگرام
URL = f'https://api.telegram.org/bot{TOKEN}/'
# لینک Web App
WEB_APP_URL = 'http://t.me/HamsterkeyReadybot/Zuzii'
DATA_FILE = 'referral_data.csv'
ALLOWED_USER_IDS = [123456789, 987654321]  # اضافه کردن آیدی‌های مجاز برای ارسال پیام
GROUP_ID = '@airdroppro_fa'
CHANNEL_ID = '@airdropbefarsi'
REQUIRED_REFERRALS = 3  # تعداد رفرال‌های لازم برای باز کردن قفل جایزه

# ایجاد فایل CSV در صورت عدم وجود آن
def create_data_file():
    if not os.path.isfile(DATA_FILE):
        with open(DATA_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['user_id', 'referral_link', 'referrals'])

# ذخیره‌سازی داده‌ها
def save_data(user_id, referral_link, referrals):
    with open(DATA_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([user_id, referral_link, referrals])

# بررسی تعداد رفرال‌ها
def check_referrals(user_id):
    if not os.path.isfile(DATA_FILE):
        create_data_file()
    referrals = 0
    with open(DATA_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 3 and int(row[0]) == user_id:
                referrals += int(row[2])
    return referrals

def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,  # تعداد کل retry ها
        backoff_factor=0.3,  # وقفه بین retry ها
        status_forcelist=(500, 502, 504),  # کدهای وضعیت HTTP که باید retry شوند
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session

session = create_session()

def send_message(chat_id, text, reply_markup=None):
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': ParseMode.HTML,  # استفاده از ParseMode.HTML به جای 'HTML'
        'disable_forwarding': True  # ممانعت از فوروارد شدن پیام
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    try:
        response = session.post(URL + 'sendMessage', json=payload)
        response.raise_for_status()
        print(f"Message sent to {chat_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to {chat_id}: {e}")
    return response

async def start(update: Update, context: CallbackContext) -> None:
    message = update.message
    user = message.from_user
    
    if user.username:
        user_mention = f"@{user.username}"
    else:
        user_mention = user.full_name

    # بررسی عضویت در گروه و کانال
    try:
        chat_member_group = await context.bot.get_chat_member(GROUP_ID, user.id)
        chat_member_channel = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        
        if chat_member_group.status not in ['member', 'administrator', 'creator']:
            await message.reply_text(
                "❗️ برای استفاده از این ربات، لطفاً ابتدا به گروه زیر بپیوندید:\n\n"
                f"🗣 گروه: {GROUP_ID}\n"
                "و سپس برای دریافت اطلاعات بیشتر به کانال زیر ملحق شوید:\n\n"
                f"📢 کانال: {CHANNEL_ID}\n"
                "بعد از عضویت در گروه و کانال، دوباره از ربات استفاده کنید.",
                parse_mode=ParseMode.HTML
            )
            return
    except Exception as e:
        print(f"Error checking group/channel membership: {e}")
        await message.reply_text("خطایی در بررسی عضویت شما در گروه یا کانال رخ داده است. لطفاً دوباره تلاش کنید.")

    # نمایش تعداد رفرال‌ها
    user_id = user.id
    referrals = check_referrals(user_id)
    
    if user.username:
        user_mention = f"@{user.username}"
    else:
        user_mention = user.full_name

    # ایجاد منوی اصلی
    main_menu_buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📥 دریافت لینک دعوت", callback_data="cb_invite"),
                InlineKeyboardButton("🎁 دریافت جایزه", callback_data="cb_get_prize")
            ]
        ]
    )

    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]
        user_info_button = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "ℹ️ مشاهده اطلاعات معرفی‌کننده",
                        callback_data=f"show_user_info_{referrer_id}",
                    )
                ]
            ]
        )
        await message.reply_text(
            f"👋 سلام {user_mention}!\n\nشما به لطف {referrer_id} به ربات ما دعوت شده‌اید. برای اطلاعات بیشتر در مورد معرفی‌کننده، لطفاً از دکمه زیر استفاده کنید.",
            reply_markup=user_info_button,
        )
        referral_link = f"https://t.me/{context.bot.username}?start={user.id}"
        save_data(referrer_id, referral_link, 1)
    else:
        await message.reply_text(
            f"سلام {user_mention}!\n\nخوش آمدید به ربات ما! شما تاکنون {referrals} نفر را به ربات معرفی کرده‌اید.\n\nبرای دعوت از دوستان خود و دریافت جوایز ویژه، لطفاً از دکمه‌های زیر استفاده کنید.",
            reply_markup=main_menu_buttons
        )

async def check_referrals_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    referrals = check_referrals(user_id)
    
    if referrals >= REQUIRED_REFERRALS:
        web_app_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🎉 دریافت جایزه", url=WEB_APP_URL)]]
        )
        await update.message.reply_text(
            "🎉 تبریک می‌گوییم! شما موفق شدید تعداد رفرال‌های لازم را جمع‌آوری کنید.\n\nحالا وقت آن است که از جایزه ویژه خود بهره‌برداری کنید. برای دریافت جایزه و استفاده از امکانات ویژه، لطفاً روی دکمه زیر کلیک کنید.",
            reply_markup=web_app_button
        )
    else:
        remaining = REQUIRED_REFERRALS - referrals
        await update.message.reply_text(f"برای دریافت جایزه، شما هنوز نیاز به {remaining} معرفی دیگر دارید.\n\nتعداد رفرال‌های کنونی شما: {referrals}")

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    
    if data == "cb_invite":
        user_id = query.from_user.id
        your_bot_name = context.bot.username
        invite_link = f"https://t.me/{your_bot_name}?start={user_id}"
        invite_link_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📎 لینک دعوت ➡️", url=invite_link)]]
        )
        await query.message.reply_text(
            f"لینک دعوت شما:\n\n`{invite_link}`\n\nبرای دعوت از دوستان، لطفاً این لینک را به اشتراک بگذارید.",
            reply_markup=invite_link_button
        )
    elif data == "cb_get_prize":
        user_id = query.from_user.id
        referrals = check_referrals(user_id)
        if referrals >= REQUIRED_REFERRALS:
            await query.message.reply_text(
                "🎁 تبریک! شما به مرحله دریافت جایزه رسیدید. با کلیک روی دکمه زیر، می‌توانید جایزه ویژه خود را دریافت کنید و از امکانات منحصر به فرد بهره‌برداری نمایید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🎁 دریافت جایزه", url=WEB_APP_URL)]]
                )
            )
        else:
            await query.message.reply_text(
                "❗️ هنوز به حد نصاب برای دریافت جایزه نرسیده‌اید. لطفاً با دعوت از دوستان بیشتر، به تعداد رفرال‌های لازم دست یابید."
            )
    elif data.startswith("show_user_info_"):
        referrer_id = int(data.split("_")[-1])
        try:
            user = await context.bot.get_chat(referrer_id)
            user_info_text = f"👤 **اطلاعات کاربر** 👤\n\n"
            user_info_text += f"🆔 شناسه: `{user.id}`\n"
            user_info_text += f"🖋 نام کاربری: @{user.username}\n" if user.username else ""
            user_info_text += f"📛 نام: {user.first_name}\n"
            user_info_text += f"📛 نام خانوادگی: {user.last_name}\n" if user.last_name else ""
            await query.message.edit_text(user_info_text)
        except Exception as e:
            print(e)
            await query.message.edit_text("خطایی در دریافت اطلاعات کاربر رخ داده است.")
    elif data == "cb_back":
        await query.message.delete()

async def admin_command(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in ALLOWED_USER_IDS:
        text = "این یک پیام آزمایشی برای کاربران مجاز است."
        for chat_id in ALLOWED_USER_IDS:
            await send_message(chat_id, text)
    else:
        await update.message.reply_text("شما مجاز به ارسال این دستور نیستید.")

def main() -> None:
    create_data_file()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check_referrals", check_referrals_command))
    application.add_handler(CommandHandler("admin_command", admin_command))  # دستور برای کاربران مجاز
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()

if __name__ == '__main__':
    main()
