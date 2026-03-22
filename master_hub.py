import os
import telebot
import pymongo
from telebot import types
import datetime
import random
import string
from flask import Flask
from threading import Thread

# --- 1. إعداد واجهة الموقع الإلكتروني (لضمان الاستمرارية على Render) ---
app = Flask('')

@app.route('/')
def home():
    # هذا ما سيظهر عند فتح رابط البوت في المتصفح
    return """
    <body style="margin:0;padding:0;background:#0f0f0f;color:#00ff00;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;">
        <div style="border:2px solid #00ff00;padding:20px;text-align:center;box-shadow:0 0 20px #00ff00;">
            <h1>🚀 Master Hub V3 is ONLINE</h1>
            <p>Cloud Server: Connected ✅</p>
            <p>Bot Status: Polling...</p>
        </div>
    </body>
    """

def run():
    # جلب المنفذ تلقائياً من الاستضافة
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. الإعدادات الأساسية (بياناتك) ---
BOT_TOKEN = "8070560190:AAFjbU4sfFLjS77uE4X_csCG-T71za3eAvg"
ADMIN_ID = 8305841557
MONGO_URI = "mongodb+srv://mfasd94_db_user:UmLYtGDdobe1HGBt@cluster0.ss2d7fa.mongodb.net/?appName=Cluster0"

client = pymongo.MongoClient(MONGO_URI)
db = client['MasterHub_V3']
users_col = db['users']
codes_col = db['promo_codes']
tools_col = db['tools'] 
lessons_col = db['lessons']

bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. وظائف الجلب من السحاب ---
def get_user(user_id, username="Unknown"):
    uid = str(user_id)
    user = users_col.find_one({"user_id": uid})
    if not user:
        user = {"user_id": uid, "name": username, "joined_at": str(datetime.date.today()), "rank": "Member", "points": 0}
        users_col.insert_one(user)
    return user

# --- 4. القائمة الرئيسية ---
@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.chat.id, message.from_user.first_name)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🛠️ أدوات مجانية", "💎 أدوات بايثون VIP")
    markup.add("📚 قسم الشروحات", "🎟️ شحن كود")
    markup.add("👤 ملفي الشخصي")
    if message.chat.id == ADMIN_ID:
        markup.add("⚙️ لوحة التحكم العليا")
    
    bot.send_message(message.chat.id, "🚀 **مرحباً بك في نظام Master Hub المطور**\nتم ربط حسابك بالسحاب ✅\nنظام الويب مفعل للاستمرارية 🌐", reply_markup=markup, parse_mode="Markdown")

# --- 5. معالجة الأزرار ---
@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    uid = str(message.chat.id)
    user = get_user(uid)

    if message.text == "🛠️ أدوات مجانية":
        tools = list(tools_col.find({"type": "free"}))
        if not tools: return bot.send_message(uid, "📭 لا توجد أدوات مجانية حالياً.")
        txt = "🎁 **الأدوات المجانية:**\n"
        for t in tools: txt += f"\n🔹 {t['name']}\n🔗 {t['link']}\n"
        bot.send_message(uid, txt)

    elif message.text == "💎 أدوات بايثون VIP":
        if user['rank'] == "VIP":
            tools = list(tools_col.find({"type": "vip"}))
            if not tools: return bot.send_message(uid, "📭 لا توجد أدوات VIP حالياً.")
            txt = "🌟 **أدوات بايثون المدفوعة:**\n"
            for t in tools: txt += f"\n🔥 {t['name']}\n🔑 الكود/الرابط: `{t['link']}`\n"
            bot.send_message(uid, txt, parse_mode="Markdown")
        else:
            bot.send_message(uid, "⚠️ هذا القسم للمشتركين VIP فقط!")

    elif message.text == "📚 قسم الشروحات":
        lessons = list(lessons_col.find())
        if not lessons: return bot.send_message(uid, "📭 لا توجد شروحات حالياً.")
        for l in lessons:
            if l.get('video_id'): bot.send_video(uid, l['video_id'], caption=f"📖 {l['title']}\n\n{l['desc']}")
            else: bot.send_message(uid, f"📖 {l['title']}\n\n{l['desc']}")

    elif message.text == "👤 ملفي الشخصي":
        bot.send_message(uid, f"👤 **معلوماتك:**\n🆔: `{uid}`\n💰: {user['points']}\n🎖️: {user['rank']}")

    elif message.text == "🎟️ شحن كود":
        msg = bot.send_message(uid, "🎟️ أرسل كود الشحن:")
        bot.register_next_step_handler(msg, process_redeem)

    elif message.text == "⚙️ لوحة التحكم العليا" and message.chat.id == ADMIN_ID:
        show_admin_panel()

# --- 6. لوحة التحكم (للمطور فقط) ---
def show_admin_panel():
    u_count = users_col.count_documents({})
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ أضف أداة", callback_data="adm_add_tool"),
        types.InlineKeyboardButton("📽️ أضف شرح", callback_data="adm_add_lesson"),
        types.InlineKeyboardButton("🎁 إنشاء كود", callback_data="adm_gen_code"),
        types.InlineKeyboardButton("📢 إذاعة للكل", callback_data="adm_broadcast")
    )
    bot.send_message(ADMIN_ID, f"📊 **إحصائيات السحاب:**\n👥 مستخدمين: {u_count}\n🌐 الحالة: متصل", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def admin_actions(call):
    if call.data == "adm_add_tool":
        msg = bot.send_message(ADMIN_ID, "أرسل اسم الأداة ثم نوعها (free/vip) ثم الرابط\nمثال:\n`أداة_صيد vip https://link.com`")
        bot.register_next_step_handler(msg, save_tool)
    elif call.data == "adm_broadcast":
        msg = bot.send_message(ADMIN_ID, "أرسل الرسالة التي تريد إرسالها لجميع المستخدمين:")
        bot.register_next_step_handler(msg, send_broadcast)

def save_tool(message):
    try:
        parts = message.text.split()
        name, t_type, link = parts[0], parts[1], parts[2]
        tools_col.insert_one({"name": name, "type": t_type.lower(), "link": link})
        bot.send_message(ADMIN_ID, "✅ تم حفظ الأداة في السحاب!")
    except: bot.send_message(ADMIN_ID, "❌ خطأ في الصيغة!")

def send_broadcast(message):
    users = users_col.find()
    count = 0
    for u in users:
        try:
            bot.send_message(u['user_id'], f"📢 **إعلان من الإدارة:**\n\n{message.text}")
            count += 1
        except: continue
    bot.send_message(ADMIN_ID, f"✅ تم إرسال الإذاعة لـ {count} مستخدم.")

def process_redeem(message):
    c = codes_col.find_one_and_update({"code": message.text, "status": "active"}, {"$set": {"status": "used"}})
    if c:
        users_col.update_one({"user_id": str(message.chat.id)}, {"$inc": {"points": c['value']}})
        bot.send_message(message.chat.id, f"✅ تم شحن {c['value']} نقطة!")
    else: bot.send_message(message.chat.id, "❌ كود غير صالح.")

# --- 7. التشغيل النهائي ---
if __name__ == "__main__":
    keep_alive() # تشغيل واجهة الويب
    print("🚀 Master Hub Bot is Live on Cloud!")
    bot.infinity_polling()
