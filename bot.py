from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ─────────────────────── ТВОИ ДАННЫЕ (уже вставлены) ───────────────────────
TOKEN = '8019204650:AAGPIYeznHcsjYDXcUDK0JpzgbS-JNrxRfM'   # твой токен
ADMIN_ID = 469347035                                           # твой chat_id
# ─────────────────────────────────────────────────────────────────────────────

bot = Bot(token=TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Order(StatesGroup):
    waiting = State()
    wall = State()
    area = State()
    extras = State()
    finish = State()
    name = State()
    city = State()
    phone = State()
    contact = State()

# Клавиатуры
def get_wall_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    walls = ["Каркас", "Газоблок", "Кирпич", "Твинблок", "Теплоблок", "Брус", "Бревно", "Пеноблок"]
    kb.add(*[KeyboardButton(text=w) for w in walls])
    return kb

def get_area_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    areas = ["до 40 м²", "40-80 м²", "80-110 м²", "110-150 м²", "150-300 м²", "более 300 м²"]
    kb.add(*[KeyboardButton(text=a) for a in areas])
    return kb

def get_extras_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("Гараж"), KeyboardButton("Бассейн"))
    kb.add(KeyboardButton("Баня/сауна"), KeyboardButton("Беседка"))
    kb.add(KeyboardButton("Нет дополнений ➜"))
    return kb

def get_finish_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("Черновая"), KeyboardButton("Предчистовая"))
    kb.add(KeyboardButton("Под ключ"), KeyboardButton("Не важно ➜"))
    return kb

def get_contact_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("Телефон"), KeyboardButton("WhatsApp"))
    kb.add(KeyboardButton("Telegram"))
    return kb

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Рассчитать стоимость"))
    await message.answer(
        "База Загородки\n\nЗаборы • Ворота • Навесы • Дома\n\n"
        "Нажмите кнопку ниже — рассчитаем стоимость строительства за 60 секунд!",
        reply_markup=kb
    )

@dp.message_handler(lambda message: message.text == "Рассчитать стоимость")
async def calc_start(message: types.Message, state: FSMContext):
    await Order.wall.set()
    await state.update_data(extras=[])
    await message.answer("Материал наружных стен:", reply_markup=get_wall_kb())

@dp.message_handler(state=Order.wall)
async def process_wall(message: types.Message, state: FSMContext):
    await state.update_data(wall=message.text)
    await Order.area.set()
    await message.answer("Площадь дома:", reply_markup=get_area_kb())

@dp.message_handler(state=Order.area)
async def process_area(message: types.Message, state: FSMContext):
    await state.update_data(area=message.text)
    await Order.extras.set()
    await message.answer("Дополнения (можно несколько):\nили «Нет дополнений ➜»", reply_markup=get_extras_kb())

@dp.message_handler(state=Order.extras)
async def process_extras(message: types.Message, state: FSMContext):
    data = await state.get_data()
    extras = data.get('extras', [])
    if message.text == "Нет дополнений ➜":
        await state.update_data(extras=[])
        await Order.finish.set()
        await message.answer("Отделка:", reply_markup=get_finish_kb())
        return
    if message.text in ["Гараж", "Бассейн", "Баня/сауна", "Беседка"]:
        if message.text not in extras:
            extras.append(message.text)
            await state.update_data(extras=extras)
        await message.answer(f"Добавлено: {message.text}\nЕщё или завершить?", reply_markup=get_extras_kb())
    else:
        await state.update_data(extras=extras)
        await Order.finish.set()
        await message.answer("Отделка:", reply_markup=get_finish_kb())

@dp.message_handler(state=Order.finish)
async def process_finish(message: types.Message, state: FSMContext):
    finish = message.text.replace("Не важно ➜", "Не важно")
    await state.update_data(finish=finish)
    await Order.name.set()
    await message.answer("Ваше ФИО:", reply_markup=ReplyKeyboardRemove())

@dp.message_handler(state=Order.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await Order.city.set()
    await message.answer("Город / населённый пункт:")

@dp.message_handler(state=Order.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await Order.phone.set()
    await message.answer("Номер телефона:")

@dp.message_handler(state=Order.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await Order.contact.set()
    await message.answer("Удобный способ связи:", reply_markup=get_contact_kb())

@dp.message_handler(state=Order.contact)
async def process_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    extras_str = ', '.join(data['extras']) if data['extras'] else '—'

    summary = (
        f"<b>Новая заявка — База Загородки</b>\n\n"
        f"Материал стен: {data['wall']}\n"
        f"Площадь: {data['area']}\n"
        f"Дополнения: {extras_str}\n"
        f"Отделка: {data['finish']}\n\n"
        f"ФИО: {data['name']}\n"
        f"Город: {data['city']}\n"
        f"Телефон: {data['phone']}\n"
        f"Связь: {data['contact']}\n\n"
        f"От: @{message.from_user.username or 'не указано'}"
    )

    await bot.send_message(ADMIN_ID, summary)
    await message.answer(
        "Заявка отправлена!\n\n"
        "Мы свяжемся с вами в течение 15 минут.\nСпасибо!",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Рассчитать ещё раз"))
    )
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)