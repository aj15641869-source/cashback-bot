from bot import bot, ADMIN_ID
import db
from telebot import types

@bot.message_handler(commands=['admin'])
def admin(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📢 Broadcast","✅ Approve Payments","❌ Reject Payments","📊 View Users")
    bot.send_message(msg.chat.id,"Admin Panel", reply_markup=kb)

# Broadcast
@bot.message_handler(func=lambda m: m.text=="📢 Broadcast")
def broadcast(msg):
    bot.send_message(msg.chat.id,"Send message to broadcast")
    bot.register_next_step_handler(msg, send_all)

def send_all(msg):
    db.cur.execute("SELECT user_id FROM users")
    for u in db.cur.fetchall():
        try: bot.send_message(u[0], msg.text)
        except: pass

# View Users
@bot.message_handler(func=lambda m: m.text=="📊 View Users")
def view_users(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    db.cur.execute("SELECT user_id, referral_count, balance FROM users")
    text = ""
    for u in db.cur.fetchall():
        text += f"ID: {u[0]}, Referrals: {u[1]}, Balance: ₹{u[2]}\n"
    bot.send_message(msg.chat.id, text)

