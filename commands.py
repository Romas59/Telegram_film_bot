import os
import re
import requests
import data
from dotenv import load_dotenv
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import URLInputFile, InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
router = Router()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")


class SearchState(StatesGroup):
    waiting_for_title = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привіт! Натисни /search, щоб почати пошук фільмів.")


@router.message(Command("help"))
async def cmd_help(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🛠 **Доступні команди:**\n\n"
        "/search — Пошук фільму\n"
        "/favourites — Улюблені фільми\n"
        "/about — Про бота\n"
        "/help — Довідка"
    )


@router.message(Command("about"))
async def cmd_about(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("ℹ️ Бот для пошуку фільмів через OMDb API та збереження в улюблені.")


@router.message(Command("favourites"))
async def cmd_favourites(message: types.Message, state: FSMContext):
    await state.clear()
    films = data.get_films()
    
    if not films:
        await message.answer("⭐ Список улюблених фільмів порожній. Скористайтесь /search для пошуку.")
        return
    
    text = "⭐ **Ваші улюблені фільми:**\nОберіть фільм, щоб переглянути або видалити:"
    
    keyboard_buttons = []
    for film in films:
        if isinstance(film, dict):
            title = film.get("title") or film.get("Title") or "Без назви"
            year = film.get("year") or film.get("Year") or "н/д"
            identifier = film.get("imdbID") or title
            button_text = f"🎬 {title} ({year})"
            keyboard_buttons.append(
                [InlineKeyboardButton(text=button_text, callback_data=f"askdel_{identifier}")]
            )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data.startswith("askdel_"))
async def ask_delete_favourite(callback: types.CallbackQuery, state: FSMContext):
    identifier = callback.data.split("_", 1)[1]
    films = data.get_films()
    
    target_film = None
    for film in films:
        if isinstance(film, dict):
            ident = film.get("imdbID") or film.get("title") or film.get("Title")
            if str(ident) == str(identifier):
                target_film = film
                break
    
    if not target_film:
        await callback.answer("Фільм не знайдено.", show_alert=True)
        return
        
    title = target_film.get("title") or target_film.get("Title") or "Без назви"
    year = target_film.get("year") or target_film.get("Year") or "н/д"
    
    text = f"⚠️ Ви дійсно хочете видалити **{title} ({year})** з улюблених?"
    
    confirm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Так, видалити", callback_data=f"delfav_{identifier}"),
                InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_favourites")
            ]
        ]
    )
    
    try:
        await callback.message.edit_text(text, reply_markup=confirm_kb, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "back_to_favourites")
async def back_to_favourites(callback: types.CallbackQuery, state: FSMContext):
    films = data.get_films()
    if not films:
        await callback.message.edit_text("⭐ Список улюблених фільмів порожній.")
        await callback.answer()
        return
        
    text = "⭐ **Ваші улюблені фільми:**\nОберіть фільм, щоб переглянути або видалити:"
    keyboard_buttons = []
    for film in films:
        if isinstance(film, dict):
            title = film.get("title") or film.get("Title") or "Без назви"
            year = film.get("year") or film.get("Year") or "н/д"
            identifier = film.get("imdbID") or title
            button_text = f"🎬 {title} ({year})"
            keyboard_buttons.append(
                [InlineKeyboardButton(text=button_text, callback_data=f"askdel_{identifier}")]
            )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("delfav_"))
async def delete_single_favourite(callback: types.CallbackQuery, state: FSMContext):
    identifier = callback.data.split("_", 1)[1]
    data.remove_film(identifier)
    
    films = data.get_films()
    if not films:
        await callback.message.edit_text("⭐ Список улюблених фільмів порожній.")
        await callback.answer("Фільм видалено!")
        return
    
    text = "⭐ **Ваші улюблені фільми:**\nОберіть фільм, щоб переглянути або видалити:"
    keyboard_buttons = []
    for film in films:
        if isinstance(film, dict):
            title = film.get("title") or film.get("Title") or "Без назви"
            year = film.get("year") or film.get("Year") or "н/д"
            ident = film.get("imdbID") or title
            button_text = f"🎬 {title} ({year})"
            keyboard_buttons.append(
                [InlineKeyboardButton(text=button_text, callback_data=f"askdel_{ident}")]
            )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception:
        pass
    
    await callback.answer("Фільм видалено з улюблених! 🗑")


@router.message(Command("search"))
async def cmd_search(message: types.Message, state: FSMContext):
    await state.set_state(SearchState.waiting_for_title)
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Завершити пошук", callback_data="cancel_search"
                )
            ]
        ]
    )
    await message.answer("Введіть назву фільму для пошуку:", reply_markup=cancel_kb)


@router.callback_query(F.data == "cancel_search")
async def cancel_search(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        if callback.message.photo:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer("❌ Пошук завершено.")
        else:
            await callback.message.edit_text("❌ Пошук завершено.")
    except Exception:
        await callback.message.answer("❌ Пошук завершено.")
    await callback.answer()


@router.message(SearchState.waiting_for_title, F.text & ~F.text.startswith("/"))
async def process_search_title(message: types.Message, state: FSMContext):
    raw_query = message.text.strip()
    query = re.sub(r"([a-zA-Zа-яА-ЯёЁ]+)(\d+)", r"\1 \2", raw_query)

    await message.answer(f"🔍 Шукаю '{query}'...")

    search_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={query}"
    res = requests.get(search_url).json()

    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Завершити пошук", callback_data="cancel_search"
                )
            ]
        ]
    )

    if res.get("Response") != "True" or not res.get("Search"):
        await message.answer(
            "❌ Фільми не знайдено. Спробуйте іншу назву:", reply_markup=cancel_kb
        )
        return

    keyboard_buttons = []
    for item in res["Search"][:8]:
        title = item.get("Title")
        year = item.get("Year")
        imdb_id = item.get("imdbID")
        button_text = f"🎬 {title} ({year})"
        keyboard_buttons.append(
            [InlineKeyboardButton(text=button_text, callback_data=f"film_{imdb_id}")]
        )

    keyboard_buttons.append(
        [InlineKeyboardButton(text="❌ Завершити пошук", callback_data="cancel_search")]
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer(
        "📋 Знайдено кілька варіантів. Оберіть потрібний:", reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("film_"))
async def select_film(callback: types.CallbackQuery, state: FSMContext):
    imdb_id = callback.data.split("_")[1]

    detail_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
    film_data = requests.get(detail_url).json()

    if film_data.get("Response") == "False":
        await callback.answer("Помилка завантаження інформації.", show_alert=True)
        return

    imdb_link = f"https://www.imdb.com/title/{imdb_id}/"

    caption = (
        f"✅ **Фільм обрано!**\n\n"
        f"🎬 **Назва:** {film_data.get('Title')}\n"
        f"📅 **Рік:** {film_data.get('Year')}\n"
        f"🎭 **Жанр:** {film_data.get('Genre')}\n"
        f"⭐ **Рейтинг:** {film_data.get('imdbRating')}\n"
        f"👥 **Актори:** {film_data.get('Actors')}\n\n"
        f"🔗 [Дивитися на IMDb]({imdb_link})"
    )

    films = data.get_films()
    is_in_fav = any(
        isinstance(f, dict) and (f.get("imdbID") == imdb_id or f.get("title") == film_data.get("Title"))
        for f in films
    )

    if is_in_fav:
        fav_button = InlineKeyboardButton(
            text="🗑 Видалити з улюблених", callback_data=f"remove_{imdb_id}"
        )
    else:
        fav_button = InlineKeyboardButton(
            text="⭐ Додати до улюблених", callback_data=f"fav_{imdb_id}"
        )

    film_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [fav_button],
            [
                InlineKeyboardButton(
                    text="❌ Завершити пошук", callback_data="cancel_search"
                )
            ]
        ]
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    poster_url = film_data.get("Poster")
    if poster_url and poster_url != "N/A":
        await callback.message.answer_photo(
            photo=URLInputFile(poster_url),
            caption=caption,
            reply_markup=film_kb,
            parse_mode="Markdown",
        )
    else:
        await callback.message.answer(
            caption, reply_markup=film_kb, parse_mode="Markdown"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("fav_"))
async def add_to_favourites_callback(callback: types.CallbackQuery, state: FSMContext):
    imdb_id = callback.data.split("_")[1]

    detail_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
    film_data = requests.get(detail_url).json()

    if film_data.get("Response") == "False":
        await callback.answer("Помилка завантаження.", show_alert=True)
        return

    films = data.get_films()
    exists = any(
        isinstance(f, dict) and f.get("imdbID") == imdb_id
        for f in films
    )

    if exists:
        await callback.answer("Цей фільм вже є в улюблених! ⭐", show_alert=True)
        return

    data.add_film(film_data)
    
    new_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Видалити з улюблених", callback_data=f"remove_{imdb_id}")],
            [InlineKeyboardButton(text="❌ Завершити пошук", callback_data="cancel_search")]
        ]
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except Exception:
        pass

    await callback.answer("Фільм успішно додано до улюблених! ⭐", show_alert=True)


@router.callback_query(F.data.startswith("remove_"))
async def remove_from_favourites_callback(callback: types.CallbackQuery, state: FSMContext):
    imdb_id = callback.data.split("_")[1]
    
    data.remove_film(imdb_id)

    new_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Додати до улюблених", callback_data=f"fav_{imdb_id}")],
            [InlineKeyboardButton(text="❌ Завершити пошук", callback_data="cancel_search")]
        ]
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
    except Exception:
        pass

    await callback.answer("Фільм видалено з улюблених! 🗑", show_alert=True)