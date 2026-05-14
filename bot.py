import json
import os
import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8634034513:AAHrw4KkjsYfNuf5eA3UWZg7b9-QWs21j6k"
RULES_LINK = "https://telegra.ph/komandy-chebureka-richa-05-11"
DATA_FILE = "data.json"
ADMIN_IDS = ["6319679398"]

# ========== ОСНОВНЫЕ ФУНКЦИИ ==========
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

# ========== РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ ==========
def register_user(data, user_id, username, first_name):
    if user_id not in data:
        if str(user_id).startswith("-"):
            return data
        real_name = first_name or f"Игрок_{user_id[-4:]}"
        data[user_id] = {
            "balance": 100,
            "username": real_name,
            "last_bonus": 0,
            "reg_time": time.time(),
            "inventory": []
        }
        save_data(data)
    return data

# ========== ВСЕ КОМАНДЫ (каждая в своей функции) ==========

async def cmd_balance(update, context, data, user_id):
    """Команда: б - баланс"""
    await update.message.reply_text(f"💰 Баланс: {data[user_id]['balance']} 🪙")

async def cmd_profile(update, context, data, user_id):
    """Команда: п - профиль"""
    balance = data[user_id]["balance"]
    level = max(1, balance // 500 + 1)
    exp_needed = level * 500
    exp_current = balance % 500
    reg_date = time.strftime("%d.%m.%Y", time.localtime(data[user_id].get("reg_time", time.time())))
    
    text = (
        f"📒 *Профиль*\n\n"
        f"👤 {data[user_id]['username']}\n"
        f"💰 {balance} 🪙\n"
        f"📈 Уровень {level}\n"
        f"⚡ Опыт {exp_current}/{exp_needed}\n"
        f"📅 С {reg_date}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_exp(update, context, data, user_id):
    """Команда: опыт - прогресс уровня"""
    balance = data[user_id]["balance"]
    level = max(1, balance // 500 + 1)
    exp_needed = level * 500
    exp_current = balance % 500
    await update.message.reply_text(
        f"📈 Уровень {level}\nОпыт {exp_current}/{exp_needed}\nДо уровня: {exp_needed - exp_current} 🪙",
        parse_mode="Markdown"
    )

async def cmd_bonus(update, context, data, user_id):
    """Команда: бонус - ежедневный бонус"""
    last = data[user_id].get("last_bonus", 0)
    now = int(time.time())
    if now - last >= 86400:
        data[user_id]["balance"] += 100
        data[user_id]["last_bonus"] = now
        save_data(data)
        await update.message.reply_text(f"🎁 +100 монет! Баланс: {data[user_id]['balance']}")
    else:
        hours = (86400 - (now - last)) // 3600
        await update.message.reply_text(f"⏰ Бонус через {hours} ч")

async def cmd_give(update, context, data, user_id):
    """Команда: дать [сумма] - перевод (ответом)"""
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответь на сообщение")
        return
    parts = update.message.text.split()
    if len(parts) != 2:
        await update.message.reply_text("❌ дать [сумма]")
        return
    try:
        amount = int(parts[1])
    except:
        await update.message.reply_text("❌ Числом!")
        return
    if amount <= 0:
        await update.message.reply_text("❌ >0")
        return
    
    target = update.message.reply_to_message.from_user
    target_id = str(target.id)
    
    if target_id == user_id:
        await update.message.reply_text("❌ Себе нельзя")
        return
    if data[user_id]["balance"] < amount:
        await update.message.reply_text(f"❌ Не хватает! Баланс: {data[user_id]['balance']}")
        return
    
    if target_id not in data:
        data[target_id] = {"balance": 100, "username": target.first_name, "last_bonus": 0, "reg_time": time.time(), "inventory": []}
    
    data[user_id]["balance"] -= amount
    data[target_id]["balance"] += amount
    save_data(data)
    await update.message.reply_text(f"✅ +{amount} → {target.first_name}\n💰 Баланс: {data[user_id]['balance']}")

async def cmd_slot(update, context, data, user_id):
    """Команда: слот - казино с кнопками"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Крутить за 10", callback_data="slot_10")],
        [InlineKeyboardButton("🎰 Крутить за 50", callback_data="slot_50")],
        [InlineKeyboardButton("🎰 Крутить за 100", callback_data="slot_100")],
        [InlineKeyboardButton("🎰 Крутить за 500", callback_data="slot_500")],
        [InlineKeyboardButton("💰 Другая ставка", callback_data="slot_custom")]
    ])
    
    await update.message.reply_text(
        f"🎰 *КАЗИНО*\n\n"
        f"💰 Твой баланс: {data[user_id]['balance']} 🪙\n\n"
        f"👇 Выбери ставку или нажми кнопку:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def slot_play(update, context, data, user_id, bet):
    """Логика игры в слоты"""
    if data[user_id]["balance"] < bet:
        await update.callback_query.answer(f"❌ Не хватает! Нужно {bet} 🪙", show_alert=True)
        return
    
    symbols = ["🍒", "🍊", "🍋", "🍉", "⭐", "💎"]
    result = [random.choice(symbols) for _ in range(3)]
    
    win = 0
    if result[0] == result[1] == result[2]:
        if result[0] == "💎":
            win = bet * 10
            win_text = f"💎 ДЖЕКПОТ! x10! +{win} 🪙"
        elif result[0] == "⭐":
            win = bet * 5
            win_text = f"⭐ СУПЕР! x5! +{win} 🪙"
        else:
            win = bet * 3
            win_text = f"🎉 УРА! x3! +{win} 🪙"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win = bet * 2
        win_text = f"✅ НЕПЛОХО! x2! +{win} 🪙"
    else:
        win = 0
        win_text = f"❌ ПРОИГРЫШ! -{bet} 🪙"
    
    if win > 0:
        data[user_id]["balance"] += win - bet
    else:
        data[user_id]["balance"] -= bet
    save_data(data)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🎰 Крутить за {bet}", callback_data=f"slot_bet_{bet}"),
            InlineKeyboardButton("💰 Изменить ставку", callback_data="slot_change")
        ]
    ])
    
    text = (
        f"🎰 *СЛОТЫ*\n\n"
        f"[ {result[0]} ] [ {result[1]} ] [ {result[2]} ]\n\n"
        f"{win_text}\n\n"
        f"💰 Баланс: {data[user_id]['balance']} 🪙\n"
    )
    
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await update.callback_query.answer()

async def slot_change_bet(update, context, data, user_id):
    """Меню выбора новой ставки"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 10 🪙", callback_data="slot_set_10")],
        [InlineKeyboardButton("🎰 50 🪙", callback_data="slot_set_50")],
        [InlineKeyboardButton("🎰 100 🪙", callback_data="slot_set_100")],
        [InlineKeyboardButton("🎰 500 🪙", callback_data="slot_set_500")],
        [InlineKeyboardButton("◀️ Назад", callback_data="slot_back")]
    ])
    
    await update.callback_query.message.edit_text(
        f"🎰 *ВЫБЕРИ СТАВКУ*\n\n"
        f"💰 Баланс: {data[user_id]['balance']} 🪙",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await update.callback_query.answer()

async def slot_set_bet(update, context, data, user_id, bet):
    """Установка ставки и начало игры"""
    if data[user_id]["balance"] < bet:
        await update.callback_query.answer(f"❌ Не хватает! Нужно {bet} 🪙", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🎰 Крутить", callback_data=f"slot_play_{bet}"),
            InlineKeyboardButton("💰 Изменить", callback_data="slot_change")
        ]
    ])
    
    await update.callback_query.message.edit_text(
        f"🎰 *СТАВКА {bet} 🪙*\n\n"
        f"💰 Баланс: {data[user_id]['balance']} 🪙\n\n"
        f"👇 Нажми КРУТИТЬ чтобы играть:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await update.callback_query.answer()        

async def cmd_shop(update, context, data, user_id):
    """Команда: магазин - список товаров"""
    text = (
        "🛍 *Магазин*\n\n"
        "🍔 Чебуречник — 500 🪙\n"
        "🧀 Жирный чебурек — 1000 🪙\n"
        "👑 Чебурек Рич — 5000 🪙\n"
        "💎 Легенда — 10000 🪙\n\n"
        "📝 купить [роль]\n"
        "📦 инв"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_buy(update, context, data, user_id):
    """Команда: купить [роль] - покупка"""
    parts = update.message.text.split()
    if len(parts) != 2:
        await update.message.reply_text("❌ купить [роль]")
        return
    
    role = parts[1].lower()
    items = {
        "чебуречник": {"name": "🍔 Чебуречник", "price": 500},
        "жирный чебурек": {"name": "🧀 Жирный чебурек", "price": 1000},
        "чебурек рич": {"name": "👑 Чебурек Рич", "price": 5000},
        "легенда": {"name": "💎 Легенда", "price": 10000}
    }
    
    if role not in items:
        await update.message.reply_text("❌ Нет такой роли! магазин")
        return
    
    item = items[role]
    if data[user_id]["balance"] < item["price"]:
        await update.message.reply_text(f"❌ Нужно {item['price']} 🪙")
        return
    
    inventory = data[user_id].get("inventory", [])
    if item["name"] in inventory:
        await update.message.reply_text("❌ Уже есть")
        return
    
    data[user_id]["balance"] -= item["price"]
    data[user_id]["inventory"].append(item["name"])
    save_data(data)
    await update.message.reply_text(f"✅ Куплено {item['name']}!\n💰 Баланс: {data[user_id]['balance']}")

async def cmd_inv(update, context, data, user_id):
    """Команда: инв - инвентарь (роли и предметы)"""
    inv = data[user_id].get("inventory", [])
    items = data[user_id].get("items", [])
    
    if not inv and not items:
        await update.message.reply_text("📦 Пусто. Открой кейс: кейсы")
        return
    
    text = "📦 *Инвентарь*\n\n"
    
    if inv:
        text += "*Роли:*\n" + "\n".join([f"• {i}" for i in inv]) + "\n\n"
    
    if items:
        text += f"*Предметы:* {len(items)} шт.\n\n👇 Нажми кнопку чтобы использовать:"
    else:
        text += "🎁 Нет предметов. Открой кейс: кейсы"
    
    if items:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Мои предметы", callback_data="show_inventory")]
        ])
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 Открыть кейс", callback_data="cases_back")]
        ])
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def cmd_promo(update, context, data, user_id):
    """Команда: промокод [код] - активация промокода"""
    parts = update.message.text.split()
    if len(parts) != 2:
        await update.message.reply_text("❌ Использование: промокод [код]")
        return
    
    code = parts[1]
    promos = data.get("promocodes", {})
    
    if code not in promos:
        await update.message.reply_text("❌ Неверный промокод!")
        return
    
    promo = promos[code]
    
    if len(promo.get("activated_by", [])) >= promo.get("uses", 1):
        await update.message.reply_text("❌ Промокод больше не действует!")
        return
    
    if user_id in promo.get("activated_by", []):
        await update.message.reply_text("❌ Ты уже активировал этот промокод!")
        return
    
    data[user_id]["balance"] += promo["reward"]
    
    if "activated_by" not in promo:
        promo["activated_by"] = []
    promo["activated_by"].append(user_id)
    
    promos[code] = promo
    data["promocodes"] = promos
    save_data(data)
    
    await update.message.reply_text(f"✅ Промокод активирован! +{promo['reward']} монет!\n💰 Баланс: {data[user_id]['balance']}")

async def cmd_business(update, context, data, user_id):
    """Команда: бизнес - показать бизнес с кнопками и ценой улучшения"""
    business = data[user_id].get("business", None)
    
    if not business:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏢 Купить бизнес (1500🪙)", callback_data="buy_business_старт")]
        ])
        await update.message.reply_text(
            "🏢 *У тебя нет бизнеса!*\n\n"
            "💰 Стоимость: 1500 🪙\n"
            "📊 Начальный доход: 50 🪙/час\n"
            "⏱ Накопление: до 24 часов\n\n"
            "👇 Купи бизнес чтобы начать:",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return
    
    level = business.get("level", 1)
    
    income_data = {
        1: 50, 2: 80, 3: 120, 4: 180, 5: 250,
        6: 350, 7: 480, 8: 640, 9: 850, 10: 1100,
        11: 1400, 12: 1800, 13: 2300, 14: 2900, 15: 3600,
        16: 4500, 17: 5600, 18: 7000, 19: 8700, 20: 11000
    }
    
    upgrade_costs = {
        1: 800, 2: 1000, 3: 1500, 4: 2000, 5: 3000,
        6: 4000, 7: 5000, 8: 7000, 9: 10000, 10: 13000,
        11: 17000, 12: 22000, 13: 28000, 14: 35000, 15: 45000,
        16: 60000, 17: 80000, 18: 100000, 19: 150000
    }
    
    income_per_hour = income_data.get(level, 50)
    last_collect = business.get("last_collect", time.time())
    
    seconds_passed = int(time.time() - last_collect)
    hours_passed = min(seconds_passed // 3600, 24)
    
    if hours_passed >= 1:
        pending = income_per_hour * hours_passed
        pending_text = f"{pending} 🪙 *(можно собрать)*"
    else:
        hours_left = 1 - (seconds_passed / 3600)
        minutes_left = int(hours_left * 60)
        pending_text = f"0 🪙 *(через {minutes_left} мин)*"
    
    if level < 20:
        next_cost = upgrade_costs.get(level, 10000)
        upgrade_text = f"{next_cost} 🪙 → уровень {level + 1}"
    else:
        upgrade_text = "🏆 МАКСИМУМ"
    
    text = (
        f"🏢 *Твой бизнес*\n\n"
        f"📊 Уровень: {level}\n"
        f"💰 Доход в час: {income_per_hour} 🪙\n"
        f"⏱ Накоплено: {pending_text}\n"
        f"📈 Максимум за 24ч: {income_per_hour * 24} 🪙\n"
        f"💸 Улучшение: {upgrade_text}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📈 Улучшить", callback_data="upgrade_business"),
            InlineKeyboardButton("💰 Собрать", callback_data="collect_income")
        ]
    ])
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)
    
async def cmd_cases(update, context, data, user_id, is_callback=False):
    """Команда: кейсы - магазин кейсов"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Обычный кейс (100🪙)", callback_data="case_normal")],
        [InlineKeyboardButton("💎 Редкий кейс (500🪙)", callback_data="case_rare")],
        [InlineKeyboardButton("👑 Легендарный кейс (2000🪙)", callback_data="case_legendary")]
    ])
    
    text = (
        "🎁 *КЕЙСЫ*\n\n"
        "📦 Обычный кейс — 100🪙 (награда 50-200)\n"
        "💎 Редкий кейс — 500🪙 (награда 300-1000)\n"
        "👑 Легендарный кейс — 2000🪙 (награда 1000-5000)\n\n"
        "👇 Выбери кейс:"
    )
    
    if is_callback:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def open_case(update, context, data, user_id, case_type):
    """Открытие кейса (сбалансированная версия)"""
    cases = {
        "normal": {"name": "📦 Обычный кейс", "price": 100, "min_reward": 30, "max_reward": 150},
        "rare": {"name": "💎 Редкий кейс", "price": 500, "min_reward": 200, "max_reward": 800},
        "legendary": {"name": "👑 Легендарный кейс", "price": 2000, "min_reward": 800, "max_reward": 3500}
    }
    
    case = cases[case_type]
    
    if data[user_id]["balance"] < case["price"]:
        await update.callback_query.answer(f"❌ Не хватает! Нужно {case['price']} 🪙", show_alert=True)
        return
    
    reward = random.randint(case["min_reward"], case["max_reward"])
    
    win_chance = random.random() < 0.3 if case_type == "normal" else (0.25 if case_type == "rare" else 0.2)
    
    if win_chance and reward < case["price"]:
        reward = reward * 2
    
    items = ["🍀 Удача", "🎰 Бесплатная ставка", "⭐ Звезда"]
    extra_item = random.choice(items) if random.random() < 0.15 else None
    
    roles = ["🍔 Чебуречник", "🧀 Жирный чебурек"]
    extra_role = random.choice(roles) if random.random() < 0.05 and case_type == "legendary" else None
    
    data[user_id]["balance"] += reward - case["price"]
    
    if extra_item:
        if "items" not in data[user_id]:
            data[user_id]["items"] = []
        data[user_id]["items"].append(extra_item)
    
    if extra_role:
        if "inventory" not in data[user_id]:
            data[user_id]["inventory"] = []
        if extra_role not in data[user_id]["inventory"]:
            data[user_id]["inventory"].append(extra_role)
    
    save_data(data)
    
    profit = reward - case["price"]
    if profit > 0:
        profit_text = f"✅ Чистый выигрыш: +{profit} 🪙"
    elif profit < 0:
        profit_text = f"❌ Чистый проигрыш: {profit} 🪙"
    else:
        profit_text = f"🤝 Вернул свои {case['price']} 🪙"
    
    reward_text = f"💰 +{reward} 🪙"
    if extra_item:
        reward_text += f"\n🎁 +{extra_item}"
    if extra_role:
        reward_text += f"\n👑 +{extra_role} (роль)"
    
    text = (
        f"🎲 *Ты открыл {case['name']}*\n\n"
        f"{reward_text}\n\n"
        f"{profit_text}\n"
        f"💎 Новый баланс: {data[user_id]['balance']} 🪙"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 Открыть ещё", callback_data=f"case_{case_type}_again")],
        [InlineKeyboardButton("◀️ Назад к кейсам", callback_data="cases_back")]
    ])
    
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await update.callback_query.answer()    

async def use_item(update, context, data, user_id, item_name):
    """Использование предмета из инвентаря"""
    items = data[user_id].get("items", [])
    
    if item_name not in items:
        await update.callback_query.answer("❌ У тебя нет этого предмета!", show_alert=True)
        return
    
    effects = {
        "🍀 Удача": {"text": "Тебе повезло! +50 🪙", "action": "money", "value": 50},
        "🎰 Бесплатная ставка": {"text": "Ты получил бесплатную ставку в казино! +100 🪙", "action": "money", "value": 100},
        "⭐ Звезда": {"text": "Звезда упала! +200 опыта", "action": "exp", "value": 200},
        "🍔 Чебурек": {"text": "Вкусный чебурек! +30 🪙", "action": "money", "value": 30},
        "🎲 Счастливый билет": {"text": "Ты выиграл в лотерею! +500 🪙", "action": "money", "value": 500}
    }
    
    effect = effects.get(item_name)
    if not effect:
        await update.callback_query.answer("❌ Этот предмет нельзя использовать!", show_alert=True)
        return
    
    if effect["action"] == "money":
        data[user_id]["balance"] += effect["value"]
        save_data(data)
        result_text = f"💰 {effect['text']}\n💎 Новый баланс: {data[user_id]['balance']} 🪙"
    
    elif effect["action"] == "exp":
        balance = data[user_id]["balance"]
        level = max(1, balance // 500 + 1)
        exp_needed = level * 500
        exp_current = balance % 500
        new_exp = exp_current + effect["value"]
        
        if new_exp >= exp_needed:
            data[user_id]["balance"] += (new_exp - exp_needed) + 500
            save_data(data)
            result_text = f"📈 {effect['text']}\n✨ Ты повысил уровень! Новый баланс: {data[user_id]['balance']} 🪙"
        else:
            data[user_id]["balance"] += effect["value"]
            save_data(data)
            result_text = f"📈 {effect['text']}\n💎 Новый баланс: {data[user_id]['balance']} 🪙"
    
    items.remove(item_name)
    data[user_id]["items"] = items
    save_data(data)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Инвентарь", callback_data="show_inventory")]
    ])
    
    await update.callback_query.message.edit_text(result_text, parse_mode="Markdown", reply_markup=keyboard)
    await update.callback_query.answer(f"✅ Ты использовал {item_name}!")

async def cmd_items(update, context, data, user_id, is_callback=False):
    """Команда: предметы - показать предметы с кнопками"""
    items = data[user_id].get("items", [])
    
    if not items:
        if is_callback:
            await update.callback_query.message.reply_text("📦 У тебя нет предметов. Открой кейс: кейсы")
        else:
            await update.message.reply_text("📦 У тебя нет предметов. Открой кейс: кейсы")
        return
    
    keyboard = []
    for item in items:
        keyboard.append([InlineKeyboardButton(f"🎁 {item}", callback_data=f"use_item_{item}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="items_back")])
    
    text = f"📦 *Твои предметы*\n\nВсего: {len(items)} шт.\n\n👇 Нажми на предмет чтобы использовать:"
    
    if is_callback:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = load_data()
    
    if user_id not in data:
        real_name = query.from_user.first_name or f"Игрок_{user_id[-4:]}"
        data[user_id] = {
            "balance": 100,
            "username": real_name,
            "last_bonus": 0,
            "reg_time": time.time(),
            "inventory": [],
            "items": []
        }
        save_data(data)
    
    callback = query.data
    
    # ========== БИЗНЕС ==========
    if callback == "buy_business_старт":
        await cmd_buy_business_callback(update, context, data, user_id, "старт")
    elif callback == "upgrade_business":
        await upgrade_business(update, context, data, user_id)
    elif callback == "collect_income":
        await collect_income(update, context, data, user_id)
    elif callback == "show_business":
        await cmd_business(update, context, data, user_id)
    
    # ========== КЕЙСЫ ==========
    elif callback == "case_normal":
        await open_case(update, context, data, user_id, "normal")
    elif callback == "case_rare":
        await open_case(update, context, data, user_id, "rare")
    elif callback == "case_legendary":
        await open_case(update, context, data, user_id, "legendary")
    elif callback == "cases_back":
        await cmd_cases(update, context, data, user_id, is_callback=True)
    elif callback == "open_cases":
        await cmd_cases(update, context, data, user_id, is_callback=True)
    elif callback.startswith("case_normal_again"):
        await open_case(update, context, data, user_id, "normal")
    elif callback.startswith("case_rare_again"):
        await open_case(update, context, data, user_id, "rare")
    elif callback.startswith("case_legendary_again"):
        await open_case(update, context, data, user_id, "legendary")
    
    # ========== ПРЕДМЕТЫ ==========
    elif callback.startswith("use_item_"):
        item_name = callback.replace("use_item_", "")
        await use_item(update, context, data, user_id, item_name)
    elif callback == "show_inventory":
        await cmd_items(update, context, data, user_id, is_callback=True)
    elif callback == "items_back":
        await cmd_cases(update, context, data, user_id, is_callback=True)
    
    # ========== КАЗИНО ==========
    elif callback == "slot_10":
        await slot_play(update, context, data, user_id, 10)
    elif callback == "slot_50":
        await slot_play(update, context, data, user_id, 50)
    elif callback == "slot_100":
        await slot_play(update, context, data, user_id, 100)
    elif callback == "slot_500":
        await slot_play(update, context, data, user_id, 500)
    elif callback == "slot_custom":
        await update.callback_query.message.reply_text("🎰 Напиши ставку числом (от 10 до 500):")
        context.user_data["awaiting_slot_bet"] = True
    elif callback.startswith("slot_direct_"):
        bet = int(callback.replace("slot_direct_", ""))
        await slot_play(update, context, data, user_id, bet)
    elif callback.startswith("slot_bet_"):
        bet = int(callback.replace("slot_bet_", ""))
        await slot_play(update, context, data, user_id, bet)
    elif callback == "slot_change":
        await slot_change_bet(update, context, data, user_id)
    elif callback.startswith("slot_set_"):
        bet = int(callback.replace("slot_set_", ""))
        await slot_set_bet(update, context, data, user_id, bet)
    elif callback == "slot_back":
        await cmd_slot(update, context, data, user_id)
    elif callback.startswith("slot_play_"):
        bet = int(callback.replace("slot_play_", ""))
        await slot_play(update, context, data, user_id, bet)

async def cmd_buy_business_callback(update, context, data, user_id, biz_key):
    """Покупка бизнеса (1 уровень за 1500 монет)"""
    if data[user_id].get("business"):
        await update.callback_query.answer("❌ У тебя уже есть бизнес!", show_alert=True)
        return
    
    if data[user_id]["balance"] < 1500:
        await update.callback_query.answer(f"❌ Не хватает! Нужно 1500 🪙", show_alert=True)
        return
    
    data[user_id]["balance"] -= 1500
    data[user_id]["business"] = {
        "level": 1,
        "last_collect": time.time()
    }
    save_data(data)
    
    text = (
        f"✅ *Ты купил бизнес!*\n\n"
        f"📊 Уровень: 1\n"
        f"💰 Доход в час: 50 🪙\n"
        f"⏱ Накопление: 24 часа\n"
        f"💸 Остаток: {data[user_id]['balance']} 🪙\n\n"
        f"📝 Напиши `бизнес` чтобы управлять"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏢 Управлять бизнесом", callback_data="show_business")]
    ])
    
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await update.callback_query.answer()

async def upgrade_business(update, context, data, user_id):
    """Улучшение бизнеса (цена растёт с уровнем)"""
    business = data[user_id].get("business")
    
    if not business:
        await update.callback_query.answer("❌ У тебя нет бизнеса!", show_alert=True)
        return
    
    current_level = business.get("level", 1)
    
    if current_level >= 20:
        await update.callback_query.answer("🏆 Бизнес уже максимального уровня!", show_alert=True)
        return
    
    upgrade_costs = {
        1: 800, 2: 1000, 3: 1500, 4: 2000, 5: 3000,
        6: 4000, 7: 5000, 8: 7000, 9: 10000, 10: 13000,
        11: 17000, 12: 22000, 13: 28000, 14: 35000, 15: 45000,
        16: 60000, 17: 80000, 18: 100000, 19: 150000
    }
    
    income_after = {
        2: 80, 3: 120, 4: 180, 5: 250, 6: 350,
        7: 480, 8: 640, 9: 850, 10: 1100, 11: 1400,
        12: 1800, 13: 2300, 14: 2900, 15: 3600, 16: 4500,
        17: 5600, 18: 7000, 19: 8700, 20: 11000
    }
    
    cost = upgrade_costs.get(current_level, 999999)
    new_level = current_level + 1
    new_income = income_after.get(new_level, 50)
    
    if data[user_id]["balance"] < cost:
        await update.callback_query.answer(f"❌ Не хватает! Нужно {cost} 🪙", show_alert=True)
        return
    
    data[user_id]["balance"] -= cost
    business["level"] = new_level
    save_data(data)
    
    text = (
        f"🏢 *Бизнес улучшен!*\n\n"
        f"📊 Уровень: {new_level}\n"
        f"💰 Доход в час: {new_income} 🪙\n"
        f"💸 Остаток: {data[user_id]['balance']} 🪙"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📈 Улучшить", callback_data="upgrade_business"),
            InlineKeyboardButton("💰 Собрать", callback_data="collect_income")
        ]
    ])
    
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await update.callback_query.answer(f"✅ Бизнес улучшен до {new_level} уровня!")
    
async def collect_income(update, context, data, user_id):
    """Сбор дохода (максимум за 24 часа)"""
    business = data[user_id].get("business")
    
    if not business:
        await update.callback_query.answer("❌ У тебя нет бизнеса!", show_alert=True)
        return
    
    level = business.get("level", 1)
    
    income_data = {
        1: 50, 2: 80, 3: 120, 4: 180, 5: 250,
        6: 350, 7: 480, 8: 640, 9: 850, 10: 1100,
        11: 1400, 12: 1800, 13: 2300, 14: 2900, 15: 3600,
        16: 4500, 17: 5600, 18: 7000, 19: 8700, 20: 11000
    }
    
    income_per_hour = income_data.get(level, 50)
    last_collect = business.get("last_collect", time.time())
    
    seconds_passed = int(time.time() - last_collect)
    hours_passed = min(seconds_passed // 3600, 24)
    
    if hours_passed < 1:
        await update.callback_query.answer("⏱ Доход будет через час!", show_alert=True)
        return
    
    total = income_per_hour * hours_passed
    
    data[user_id]["balance"] += total
    business["last_collect"] = time.time()
    save_data(data)
    
    text = (
        f"🏢 *Твой бизнес*\n\n"
        f"📊 Уровень: {level}\n"
        f"💰 Доход в час: {income_per_hour} 🪙\n"
        f"⏱ Накоплено: 0 🪙\n"
        f"📈 Собрано: {total} 🪙"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📈 Улучшить", callback_data="upgrade_business"),
            InlineKeyboardButton("💰 Собрать", callback_data="collect_income")
        ]
    ])
    
    await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await update.callback_query.answer(f"✅ Ты собрал {total} 🪙!")

async def cmd_my_promos(update, context, data, user_id):
    """Команда: моипромокоды - список активированных промокодов"""
    promos = data.get("promocodes", {})
    my_codes = []
    
    for code, promo in promos.items():
        if user_id in promo.get("activated_by", []):
            my_codes.append(f"• {code} (+{promo['reward']}🪙)")
    
    if my_codes:
        await update.message.reply_text(f"📜 *Активированные промокоды:*\n" + "\n".join(my_codes), parse_mode="Markdown")
    else:
        await update.message.reply_text("📜 У тебя нет активированных промокодов")

async def cmd_create_promo(update, context, data, user_id):
    """Команда: создатьпромо [код] [монеты] - только админ"""
    if not is_admin(user_id):
        await update.message.reply_text("❌ Только для админа!")
        return
    
    parts = update.message.text.split()
    if len(parts) != 3:
        await update.message.reply_text("❌ Использование: создатьпромо [код] [монеты]")
        return
    
    code = parts[1]
    try:
        reward = int(parts[2])
    except:
        await update.message.reply_text("❌ Монеты должны быть числом!")
        return
    
    promos = data.get("promocodes", {})
    promos[code] = {
        "reward": reward,
        "uses": 10,
        "activated_by": []
    }
    data["promocodes"] = promos
    save_data(data)
    
    await update.message.reply_text(f"✅ Промокод {code} создан! Награда: {reward} монет, лимит: 10 использований")

# ========== СЛОВАРЬ КОМАНД ==========
COMMANDS = {
    "б": cmd_balance,
    "п": cmd_profile,
    "опыт": cmd_exp,
    "бонус": cmd_bonus,
    "дать": cmd_give,
    "слот": cmd_slot,
    "магазин": cmd_shop,
    "купить": cmd_buy,
    "инв": cmd_inv,
    "промокод": cmd_promo,
    "моипромокоды": cmd_my_promos,
    "создатьпромо": cmd_create_promo,
    "бизнес": cmd_business,
    "кейсы": cmd_cases,
    "предметы": cmd_items,
}

# ========== ОБРАБОТЧИК ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    if not user:
        return
    
    user_id = str(user.id)
    text = update.message.text.strip().lower()
    
    data = load_data()
    data = register_user(data, user_id, user.username, user.first_name)
    
    if context.user_data.get("awaiting_slot_bet"):
        try:
            bet = int(text)
            if 10 <= bet <= 500:
                del context.user_data["awaiting_slot_bet"]
                
                if data[user_id]["balance"] < bet:
                    await update.message.reply_text(f"❌ Не хватает! Нужно {bet} 🪙")
                    return
                
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(f"🎰 Крутить", callback_data=f"slot_direct_{bet}"),
                        InlineKeyboardButton("💰 Изменить ставку", callback_data="slot_change")
                    ]
                ])
                
                await update.message.reply_text(
                    f"🎰 *СТАВКА {bet} 🪙*\n\n"
                    f"💰 Баланс: {data[user_id]['balance']} 🪙\n\n"
                    f"👇 Нажми КРУТИТЬ чтобы играть:",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            else:
                await update.message.reply_text("❌ Ставка должна быть от 10 до 500!")
        except ValueError:
            await update.message.reply_text("❌ Введи число!")
        return
    
    for cmd_prefix, cmd_func in COMMANDS.items():
        if text == cmd_prefix or text.startswith(f"{cmd_prefix} "):
            await cmd_func(update, context, data, user_id)
            return

# ========== СТАНДАРТНЫЕ КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🎉 Привет, {user.first_name}!\n"
        f"Добро пожаловать в «Чебурек Рич»!\n"
        f"💰 Старт: 100 монет\n"
        f"/help - все команды"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📖 *Команды*\n\n"
        f"Список в статье:\n👉 {RULES_LINK}",
        parse_mode="Markdown"
    )

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    
    data = load_data()
    
    if not data:
        await update.message.reply_text("📊 Пока нет зарегистрированных игроков!")
        return
    
    filtered_data = {}
    for user_id, user_data in data.items():
        balance = user_data.get("balance", 0)
        name = user_data.get("username", "")
        
        if str(user_id).startswith("-"):
            continue
        if name.lower() in ["telegram", "group", "bot", ""]:
            continue
        if balance <= 0:
            continue
        
        filtered_data[user_id] = user_data
    
    if not filtered_data:
        await update.message.reply_text("📊 Пока нет игроков с балансом!")
        return
    
    sorted_players = sorted(filtered_data.items(), key=lambda x: x[1].get("balance", 0), reverse=True)
    top_10 = sorted_players[:10]
    
    if not top_10:
        await update.message.reply_text("📊 Топ пуст!")
        return
    
    message = "🏆 *Топ богачей* 🏆\n\n"
    
    for i, (user_id, user_data) in enumerate(top_10, 1):
        name = user_data.get("username", f"Игрок_{user_id[-4:]}")
        balance = user_data.get("balance", 0)
        
        if i == 1:
            medal = "👑"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = "📌"
        
        message += f"{medal} {i}. {name} — {balance} 🪙\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
