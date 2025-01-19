from aiogram import Router, types
from aiogram.filters import Command
from keyboard import main_keyboard
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from functions.utilits import log_workout, get_food_info, check_progress,send_progress_charts, calculate_needs, log_water
from users import user_profiles
from config import OPENWEATHER_API_KEY
import requests
from aiogram.types import Message
import requests
from aiogram.filters import Command
from aiogram import types

router = Router()


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "Вот список доступных команд:\n"
        "/set_profile - Настроить профиль\n"
        "/log_water  - Записать количество воды\n"
        "/log_food  - Записать потребление пищи\n"
        "/log_workout <тип тренировки> <время в минутах> - Записать тренировку\n"
        "/check_progress - Проверить прогресс\n"
    )
    await message.reply(help_text, reply_markup=main_keyboard)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    start_text = "Добро пожаловать! Выберите действие из меню ниже."
    await message.reply(start_text, reply_markup=main_keyboard)

@router.message(Command('set_profile'))
async def set_profile(message: Message):
    await message.reply("Введите ваш вес (в кг):")
    user_profiles[message.from_user.id] = {}
    user_profiles[message.from_user.id]['state'] = 'weight'

@router.message(Command('log_water'))
async def log_water_handler(message: Message):
    user_id = message.from_user.id
    try:
        command_args = message.text.split()
        if len(command_args) < 2:
            await message.reply("Пожалуйста, укажите количество воды в формате: `/log_water <количество>`.")
            return

        amount = float(command_args[1])
        if amount <= 0:
            await message.reply("Количество воды должно быть положительным числом.")
            return

        # Обновляем прогресс воды
        remaining = log_water(user_id, amount)  
        await message.reply(
            f"Вы выпили {amount} л воды. Осталось до нормы: {remaining:.2f} л."
        )
    except ValueError:
        await message.reply("Пожалуйста, введите количество воды в виде числа, например: `/log_water 1.5`.")
    except Exception as e:
        await message.reply("Произошла ошибка при обработке команды. Попробуйте еще раз.")
        print(f"Ошибка в log_water_handler: {e}")

@router.message(Command('log_food'))
async def log_food_handler(message: Message):
    user_id = message.from_user.id

    # Проверяем, есть ли профиль пользователя
    if user_id not in user_profiles:
        user_profiles[user_id] = {} 

    # Запрашиваем у пользователя название продукта
    await message.reply("Введите название продукта для поиска.")
    user_profiles[user_id]['state'] = 'waiting_for_food_name'

@router.message(lambda message: user_profiles.get(message.from_user.id, {}).get('state') == 'waiting_for_food_name')
async def handle_food_name(message: Message):
    user_id = message.from_user.id
    food_name = message.text.strip()
    food_data = get_food_info(food_name)

    if food_data:
        calories_per_100g = food_data['calories']
        user_profiles[user_id]['food_name'] = food_data['name']
        user_profiles[user_id]['calories_per_100g'] = calories_per_100g
        user_profiles[user_id]['state'] = 'waiting_for_food_amount'

        await message.reply(
            f"{food_data['name']} — {calories_per_100g} ккал на 100 г. Сколько грамм вы съели?"
        )
    else:
        await message.reply("Информация о продукте не найдена. Попробуйте ввести другой продукт.")

# Обработчик ввода количества граммов
@router.message(lambda message: user_profiles.get(message.from_user.id, {}).get('state') == 'waiting_for_food_amount')
async def handle_food_amount(message: Message):
    user_id = message.from_user.id

    try:
        grams = float(message.text.strip())
        calories_per_100g = user_profiles[user_id].get('calories_per_100g', 0)
        total_calories = (grams / 100) * calories_per_100g

        # Сохраняем количество потребленных калорий
        if 'calories_consumed' not in user_profiles[user_id]:
            user_profiles[user_id]['calories_consumed'] = 0
        user_profiles[user_id]['calories_consumed'] += total_calories

        await message.reply(
            f"Записано: {total_calories:.2f} ккал ({grams} г {user_profiles[user_id]['food_name']})."
        )
        user_profiles[user_id]['state'] = None
    except ValueError:
        await message.reply("Пожалуйста, введите количество граммов в виде числа.")


@router.message(Command('log_workout'))
async def log_workout_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_profiles:
        await message.reply("Сначала настройте профиль с помощью команды /set_profile.")
        return

    try:
        
        args = message.text.split()
        workout_type = args[1]
        duration = int(args[2])  # Продолжительность в минутах

        # Логика обработки тренировки
        calories_burned, water_additional = log_workout(user_id, workout_type, duration)

        await message.reply(
            f"Вы выполнили тренировку: {workout_type} на {duration} минут.\n"
            f"Сожжено калорий: {calories_burned:.0f} ккал.\n"
            f"Дополнительно выпейте воды: {water_additional:.2f} л."
        )
    except IndexError:
        await message.reply("Пожалуйста, укажите тип тренировки и продолжительность в минутах. Пример:\n"
                            "/log_workout run 30")
    except ValueError:
        await message.reply("Продолжительность тренировки должна быть числом. Пример:\n"
                            "/log_workout run 30")


@router.message(Command('check_progress'))
async def check_progress_handler(message: Message):
    user_id = message.from_user.id
    if user_id not in user_profiles:
        await message.reply("Сначала настройте профиль с помощью команды /set_profile.")
        return

    # Получение данных о прогрессе
    water_consumed, water_remaining, calories_consumed, calories_burned, calorie_remaining = check_progress(user_id)

    await message.reply(
        f"📊 Прогресс:\n"
        f"Вода:\n"
        f"- Выпито: {water_consumed:.2f} л из {user_profiles[user_id]['water_needs']:.2f} л.\n"
        f"- Осталось: {water_remaining:.2f} л.\n\n"
        f"Калории:\n"
        f"- Потреблено: {calories_consumed:.0f} ккал из {user_profiles[user_id]['calorie_needs']:.0f} ккал.\n"
        f"- Сожжено: {calories_burned:.0f} ккал.\n"
        f"- Баланс: {calorie_remaining:.0f} ккал."
    )

    await send_progress_charts(message, water_consumed, water_remaining, calories_consumed, calories_burned, user_profiles[user_id]['water_needs'], user_profiles[user_id]['calorie_needs'])


@router.message()
async def handle_message(message: Message):
    user_id = message.from_user.id

    if user_id in user_profiles and 'state' in user_profiles[user_id]:
        state = user_profiles[user_id]['state']

        if state == 'weight':
            try:
                user_profiles[user_id]['weight'] = float(message.text)
                user_profiles[user_id]['state'] = 'height'
                await message.reply("Введите ваш рост (в см):")
            except ValueError:
                await message.reply("Пожалуйста, введите число.")

        elif state == 'height':
            try:
                user_profiles[user_id]['height'] = float(message.text)
                user_profiles[user_id]['state'] = 'age'
                await message.reply("Введите ваш возраст (в годах):")
            except ValueError:
                await message.reply("Пожалуйста, введите число.")

        elif state == 'age':
            try:
                user_profiles[user_id]['age'] = int(message.text)
                user_profiles[user_id]['state'] = 'activity'
                await message.reply("Сколько минут в день вы уделяете физической активности?:")
            except ValueError:
                await message.reply("Пожалуйста, введите число.")

        elif state == 'activity':
            try:
                user_profiles[user_id]['activity'] = int(message.text)
                user_profiles[user_id]['state'] = 'city'
                await message.reply("Введите ваш город для учёта температуры:")
            except ValueError:
                await message.reply("Пожалуйста, введите число.")

        elif state == 'city':
            city = message.text

            try:
                response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric")
                response.raise_for_status()
                weather_data = response.json()
                temperature = weather_data['main']['temp']

                user_profiles[user_id]['city'] = city
                user_profiles[user_id]['temperature'] = temperature

                weight = user_profiles[user_id]['weight']
                height = user_profiles[user_id]['height']
                age = user_profiles[user_id]['age']
                activity = user_profiles[user_id]['activity']

                water_needs, calorie_needs = calculate_needs(weight, height, age, activity, temperature)

                user_profiles[user_id]['water_needs'] = water_needs
                user_profiles[user_id]['calorie_needs'] = calorie_needs

                await message.reply(
                    f"Профиль настроен! \n"
                    f"Ваши дневные нормы:\n"
                    f"- Вода: {water_needs:.2f} л\n"
                    f"- Калории: {calorie_needs:.0f} ккал"
                )
                user_profiles[user_id]['state'] = None

            except requests.RequestException:
                await message.reply("Не удалось получить данные о погоде. Попробуйте снова.")
