import telebot
from telebot import types
import db
import datetime

BOT_TOKEN = "8578243284:AAGSt3ATP-rRZaNHvFriQgO3OjzK-i8l9Wc"
ADMIN_ID = 5766303284

bot = telebot.TeleBot(BOT_TOKEN)

# ---------------------- Helpers ----------------------
def check_join(user_id):
    db.cur.execute("SELECT channel_id FROM channels")
    for ch in db.cur.fetchall():
        try:
            member = bot.get_chat_member(ch[0], user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

def main_menu(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💰 Submit Payment", "📊 Check Status")
    kb.row("👫 Invite Friends", "💵 My Balance")
    bot.send_message(msg.chat.id,"Choose an option:", reply_markup=kb)

# ---------------------- Commands ----------------------
@bot.message_handler(commands=['start'])
def start(msg):
    ref = msg.text.split(" ")[1] if len(msg.text.split()) > 1 else None

    # Save user
    try:
        db.cur.execute("INSERT INTO users(user_id,referred_by,joined_date) VALUES (?,?,?)",
                       (msg.from_user.id, ref, str(datetime.datetime.now())))
        db.conn.commit()
        if ref:
            db.cur.execute("UPDATE users SET referral_count = referral_count + 1 WHERE user_id=?", (ref,))
            db.conn.commit()
    except:
        pass

    # Force join check
    if not check_join(msg.from_user.id):
        kb = types.InlineKeyboardMarkup()
        db.cur.execute("SELECT invite FROM channels")
        for ch in db.cur.fetchall():
            kb.add(types.InlineKeyboardButton("Join Channel", url=ch[0]))
        bot.send_message(msg.chat.id,"⚠️ Please join the channels to continue", reply_markup=kb)
        return

    # Phone verification
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("📱 Verify Phone", request_contact=True))
    bot.send_message(msg.chat.id,"👋 Welcome to *Cashback Bot*\nVerify your phone number to continue",
                     reply_markup=kb, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def save_phone(msg):
    phone = msg.contact.phone_number
    try:
        db.cur.execute("UPDATE users SET phone=? WHERE user_id=?",
                       (phone, msg.from_user.id))
        db.conn.commit()
        bot.send_message(msg.chat.id,"✅ Phone Verified")
        main_menu(msg)

        # Auto referral reward
        db.cur.execute("SELECT referred_by FROM users WHERE user_id=?", (msg.from_user.id,))
        ref = db.cur.fetchone()[0]
        if ref:
            reward = 10  # ₹10 per referral
            db.cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (reward, ref))
            db.conn.commit()
            try:
                bot.send_message(ref, f"🎉 You earned ₹{reward} for referring @{msg.from_user.username or msg.from_user.first_name}!")
            except: pass
    except:
        bot.send_message(msg.chat.id,"❌ One phone = one user only")

# ---------------------- Payment ----------------------
@bot.message_handler(func=lambda m: m.text=="💰 Submit Payment")
def submit_payment(msg):
    bot.send_message(msg.chat.id,"Send Transaction ID:")
    bot.register_next_step_handler(msg, get_txn)

def get_txn(msg):
    txn = msg.text
    bot.send_message(msg.chat.id,"Send Payment Screenshot")
    bot.register_next_step_handler(msg, get_proof, txn)

def get_proof(msg, txn):
    file_id = msg.photo[-1].file_id
    db.cur.execute("INSERT INTO payments VALUES (?,?,?,?)",
                   (msg.from_user.id, txn, file_id, "Pending"))
    db.conn.commit()
    bot.send_message(msg.chat.id,"⏳ Payment submitted. Wait for approval")

# ---------------------- Referral ----------------------
@bot.message_handler(func=lambda m: m.text=="👫 Invite Friends")
def invite(msg):
    link = f"https://t.me/YOUR_BOT_USERNAME?start={msg.from_user.id}"
    bot.send_message(msg.chat.id,f"Share this link and earn rewards:\n{link}")

# ---------------------- Balance ----------------------
@bot.message_handler(func=lambda m: m.text=="💵 My Balance")
def show_balance(msg):
    db.cur.execute("SELECT balance FROM users WHERE user_id=?", (msg.from_user.id,))
    bal = db.cur.fetchone()[0]
    bot.send_message(msg.chat.id,f"💰 Your current referral balance: ₹{bal}")

# ---------------------- Status ----------------------
@bot.message_handler(func=lambda m: m.text=="📊 Check Status")
def status(msg):
    db.cur.execute("SELECT txn_id, status FROM payments WHERE user_id=?", (msg.from_user.id,))
    data = db.cur.fetchall()
    if not data:
        bot.send_message(msg.chat.id,"No payments submitted")
        return
    text = "\n".join([f"{d[0]} → {d[1]}" for d in data])
    bot.send_message(msg.chat.id,text)

bot.infinity_polling()

