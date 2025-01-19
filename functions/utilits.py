import requests
import matplotlib.pyplot as plt
from users import user_profiles
import os
import tempfile
from aiogram import types
from aiogram.types import InputFile

def is_profile_complete(user_id):
    user_data = user_profiles.get(user_id, {})
    required_fields = ['weight', 'height', 'age', 'activity', 'city', 'temperature']
    return all(field in user_data for field in required_fields)



def calculate_needs(weight, height, age, activity, temperature):
    water_needs = weight * 0.03 + (temperature - 20) * 0.01 if temperature > 20 else weight * 0.03
    bmr = 10 * weight + 6.25 * height - 5 * age + 5
    calorie_needs = bmr * (1.2 + activity * 0.03)
    return water_needs, calorie_needs

def log_water(user_id, amount):

    if 'water_consumed' not in user_profiles[user_id]:
        user_profiles[user_id]['water_consumed'] = 0

    # Обновление количества выпитой воды
    user_profiles[user_id]['water_consumed'] += amount

    
    remaining = user_profiles[user_id]['water_needs'] - user_profiles[user_id]['water_consumed']
    return max(0, remaining)  

def log_workout(user_id, workout_type, duration):
    
    # Пример расхода калорий на разные виды тренировок (ккал/мин)
    workout_calories = {
        'run': 10,  # Бег
        'walk': 2,  # Ходьба
        'cycle': 9,  # Велосипед
        'swim': 12, # Плавание
        'tennis': 12,  # Теннис
        'yoga': 4,    # Йога
    }
    
    
    workout_water = {
        'run': 0.3,
        'walk': 0.2,
        'cycle': 0.25,
        'swim': 0.35,
        'tennis': 0.35,
        'yoga': 0.15
    }
    
    # Учет калорий
    calories_burned = workout_calories.get(workout_type, 6) * duration  # По умолчанию 6 ккал/мин
    water_additional = (duration / 30) * workout_water.get(workout_type, 0.2)  # По умолчанию 200 мл за 30 мин
    
    # Обновление профиля пользователя
    if 'calories_burned' not in user_profiles[user_id]:
        user_profiles[user_id]['calories_burned'] = 0
    user_profiles[user_id]['calories_burned'] += calories_burned

    if 'water_consumed' not in user_profiles[user_id]:
        user_profiles[user_id]['water_consumed'] = 0
    user_profiles[user_id]['water_consumed'] += water_additional

    return calories_burned, water_additional

def check_progress(user_id):

    water_consumed = user_profiles[user_id].get('water_consumed', 0)
    water_needs = user_profiles[user_id]['water_needs']
    calories_consumed = user_profiles[user_id].get('calories_consumed', 0)
    calories_burned = user_profiles[user_id].get('calories_burned', 0)
    calorie_goal = user_profiles[user_id]['calorie_needs']

    water_remaining = water_needs - water_consumed
    calorie_balance = calories_consumed - calories_burned
    calorie_remaining = calorie_goal - calorie_balance

    return water_consumed, water_remaining, calories_consumed, calories_burned, calorie_remaining

def get_food_info(product_name):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        products = data.get('products', [])
        if products:
            first_product = products[0]
            return {
                'name': first_product.get('product_name', 'Неизвестно'),
                'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
            }
    except requests.RequestException:
        print("Ошибка при запросе данных о продукте.")
    return None


def send_progress_charts(message: types.Message, water_consumed, water_remaining, calories_consumed, calories_burned, water_needs, calorie_needs):
    # Создание графика для воды
    plt.figure(figsize=(10, 5))
    plt.bar(['Выпито', 'Осталось'], [water_consumed, water_remaining], color=['blue', 'lightblue'])
    plt.axhline(y=water_needs, color='r', linestyle='--', label='Цель (л)')
    plt.title('Прогресс потребления воды')
    plt.ylabel('Литры')
    plt.legend()
    plt.grid()

    # Создание временного файла для графика воды
    water_fd, water_file_path = tempfile.mkstemp(suffix='.png')  
    os.close(water_fd) 

    
    plt.savefig(water_file_path)
    plt.close()

    
    with open(water_file_path, 'rb') as water_file:
        message.answer_photo(photo=InputFile(water_file), caption='График прогресса потребления воды')

   
    os.remove(water_file_path)

    # Создание графика для калорий
    plt.figure(figsize=(10, 5))
    plt.bar(['Потреблено', 'Сожжено', 'Баланс'], [calories_consumed, calories_burned, calorie_needs - (calories_consumed - calories_burned)], color=['green', 'orange', 'lightgreen'])
    plt.axhline(y=calorie_needs, color='r', linestyle='--', label='Цель (ккал)')
    plt.title('Прогресс потребления калорий')
    plt.ylabel('Ккал')
    plt.legend()
    plt.grid()

    # Создание временного файла для графика калорий
    calories_fd, calories_file_path = tempfile.mkstemp(suffix='.png')  
    os.close(calories_fd)  


    plt.savefig(calories_file_path)
    plt.close()

  
    with open(calories_file_path, 'rb') as calories_file:
        message.answer_photo(photo=InputFile(calories_file), caption='График прогресса потребления калорий')

   
    os.remove(calories_file_path)