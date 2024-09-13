from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random

# Telegram bot token
TOKEN = '7463998284:AAG11HTANBkikMF1qO65pjZ_r3IS6SpjlKU'

# Database setup
DATABASE_URL = "sqlite:///voltronix_bot.db"
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    tokens = Column(Integer, default=0)
    current_page = Column(Integer, default=0)

class Link(Base):
    __tablename__ = 'links'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    visited = Column(Boolean, default=False)
    user_id = Column(Integer)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Telegram bot handlers
def start(update: Update, context: CallbackContext) -> None:
    session = Session()
    user_id = update.effective_user.id
    user = session.query(User).filter_by(telegram_id=user_id).first()
    
    if not user:
        user = User(telegram_id=user_id, tokens=0)
        session.add(user)
        session.commit()
    
    keyboard = [
        [InlineKeyboardButton("Watch", callback_data='watch')],
        [InlineKeyboardButton("Next", callback_data='next')],
        [InlineKeyboardButton("Balance", callback_data='balance')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please solve this problem to prove you are human: 5 + 3 = ?')

    context.user_data['verification_answer'] = 8
    context.user_data['main_menu'] = reply_markup

def verify_human(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    if int(user_input) == context.user_data['verification_answer']:
        update.message.reply_text("You are verified! Choose an option:", reply_markup=context.user_data['main_menu'])
    else:
        update.message.reply_text("Verification failed! Please try again. Type the answer:")

def watch(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    session = Session()
    user_id = update.effective_user.id
    user = session.query(User).filter_by(telegram_id=user_id).first()
    
    links = session.query(Link).filter_by(user_id=user.id, visited=False).limit(10).all()
    if not links:
        query.edit_message_text(text="No more links available.")
        return
    
    link_text = '\n'.join([f"{i+1}. {link.url}" for i, link in enumerate(links)])
    query.edit_message_text(text=f"Links to watch:\n{link_text}")

    for link in links:
        link.visited = True
    user.tokens += len(links)
    session.commit()

def next_page(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    session = Session()
    user_id = update.effective_user.id
    user = session.query(User).filter_by(telegram_id=user_id).first()
    
    links = session.query(Link).filter_by(user_id=user.id, visited=False).limit(10).all()
    if not links:
        query.edit_message_text(text="No more links available.")
        return

    link_text = '\n'.join([f"{i+1}. {link.url}" for i, link in enumerate(links)])
    query.edit_message_text(text=f"Links to watch:\n{link_text}")

def balance(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    session = Session()
    user_id = update.effective_user.id
    user = session.query(User).filter_by(telegram_id=user_id).first()
    
    query.edit_message_text(text=f"You have {user.tokens} VOLX tokens.")

def main() -> None:
    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, verify_human))
    dispatcher.add_handler(CallbackQueryHandler(watch, pattern='^watch$'))
    dispatcher.add_handler(CallbackQueryHandler(next_page, pattern='^next$'))
    dispatcher.add_handler(CallbackQueryHandler(balance, pattern='^balance$'))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
