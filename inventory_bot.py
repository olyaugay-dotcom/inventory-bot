"""
Простой Telegram-бот для учёта товара (магазин одежды).

Что умеет:
/add НАЗВАНИЕ КОЛИЧЕСТВО ЦЕНА  — добавить товар на склад
/sell НАЗВАНИЕ КОЛИЧЕСТВО      — продать товар (списать со склада)
/stock                          — показать весь остаток товара
/remove НАЗВАНИЕ                — удалить товар полностью

Данные хранятся в файле inventory.db (SQLite) — не теряются при перезапуске.
"""

import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DB_FILE = "inventory.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            name TEXT PRIMARY KEY,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.args[0]
        qty = int(context.args[1])
        price = float(context.args[2])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "Формат: /add название количество цена\nПример: /add футболка_белая 20 50000"
        )
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM items WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE items SET quantity = quantity + ?, price = ? WHERE name = ?",
                    (qty, price, name))
    else:
        cur.execute("INSERT INTO items (name, quantity, price) VALUES (?, ?, ?)",
                    (name, qty, price))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Добавлено: {name} — {qty} шт. по {price}")


async def sell_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.args[0]
        qty = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("Формат: /sell название количество\nПример: /sell футболка_белая 2")
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM items WHERE name = ?", (name,))
    row = cur.fetchone()

    if not row:
        await update.message.reply_text(f"Товар '{name}' не найден на складе.")
        conn.close()
        return

    current_qty = row[0]
    if current_qty < qty:
        await update.message.reply_text(f"Недостаточно товара. На складе: {current_qty} шт.")
        conn.close()
        return

    cur.execute("UPDATE items SET quantity = quantity - ? WHERE name = ?", (qty, name))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Продано: {name} — {qty} шт. Осталось: {current_qty - qty} шт.")


async def show_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT name, quantity, price FROM items ORDER BY name")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Склад пуст.")
        return

    lines = ["📦 Остаток товара:\n"]
    total_value = 0
    for name, qty, price in rows:
        lines.append(f"{name}: {qty} шт. × {price} = {qty * price}")
        total_value += qty * price
    lines.append(f"\nОбщая стоимость склада: {total_value}")

    await update.message.reply_text("\n".join(lines))


async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.args[0]
    except IndexError:
        await update.message.reply_text("Формат: /remove название")
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE name = ?", (name,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Товар '{name}' удалён со склада.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот учёта товара. Команды:\n"
        "/add название количество цена\n"
        "/sell название количество\n"
        "/stock\n"
        "/remove название"
    )


def main():
    init_db()

    # ВСТАВЬ СЮДА СВОЙ ТОКЕН ОТ BotFather
    TOKEN = "ВСТАВЬ_СЮДА_ТОКЕН"

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_item))
    app.add_handler(CommandHandler("sell", sell_item))
    app.add_handler(CommandHandler("stock", show_stock))
    app.add_handler(CommandHandler("remove", remove_item))

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
