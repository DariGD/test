from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/set_profile"), KeyboardButton(text="/log_water")],
        [KeyboardButton(text="/log_food"), KeyboardButton(text="/log_workout")],
        [KeyboardButton(text="/check_progress"), KeyboardButton(text="/help")],
    ],
    resize_keyboard=True
)