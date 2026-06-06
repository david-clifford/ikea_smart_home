import os
import re
import asyncio
from dotenv import load_dotenv
from dirigera import Hub
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load credentials
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DIRIGERA_TOKEN = os.getenv("DIRIGERA_TOKEN")
DIRIGERA_IP = os.getenv("DIRIGERA_IP")
ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", "0"))

hub = Hub(token=DIRIGERA_TOKEN, ip_address=DIRIGERA_IP)

# Track active timers so we can cancel them if needed
active_timers: dict[str, asyncio.Task] = {}


def parse_duration(text: str) -> int | None:
    """Parse duration string like '30m', '2h', '1h30m' into seconds."""
    total = 0
    matches = re.findall(r'(\d+)\s*(h|m|s)', text.lower())
    if not matches:
        return None
    for value, unit in matches:
        value = int(value)
        if unit == 'h':
            total += value * 3600
        elif unit == 'm':
            total += value * 60
        elif unit == 's':
            total += value
    return total if total > 0 else None


async def go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /go <outlet_name> <duration> command."""
    # Auth check
    if ALLOWED_USER_ID and update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /go <plug_name> <duration>\nExample: /go P1 30m")
        return

    outlet_name = args[0]
    duration_str = args[1]
    seconds = parse_duration(duration_str)

    if seconds is None:
        await update.message.reply_text(f"Couldn't parse duration: '{duration_str}'\nExamples: 30m, 2h, 1h30m")
        return

    # Find the outlet
    outlet = hub.get_outlet_by_name(outlet_name)
    if outlet is None:
        await update.message.reply_text(f"No outlet found named '{outlet_name}'")
        return

    # Cancel any existing timer for this outlet
    timer_key = outlet_name.lower()
    if timer_key in active_timers and not active_timers[timer_key].done():
        active_timers[timer_key].cancel()

    # Turn on
    outlet.set_on(outlet_on=True)

    # Format duration for display
    hours, remainder = divmod(seconds, 3600)
    mins, secs = divmod(remainder, 60)
    display = ""
    if hours:
        display += f"{hours}h"
    if mins:
        display += f"{mins}m"
    if secs:
        display += f"{secs}s"

    await update.message.reply_text(f"✅  {outlet_name} ON for {display}")

    # Schedule turn-off
    async def turn_off():
        await asyncio.sleep(seconds)
        outlet.set_on(outlet_on=False)
        await update.message.reply_text(f"⏰  {outlet_name} OFF (timer expired)")

    active_timers[timer_key] = asyncio.create_task(turn_off())


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command — list all outlets."""
    if ALLOWED_USER_ID and update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return

    outlets = hub.get_outlets()
    if not outlets:
        await update.message.reply_text("No outlets found.")
        return

    lines = []
    for o in outlets:
        state = "ON" if o.attributes.is_on else "OFF"
        name = o.attributes.custom_name
        timer = "⏳  timer active" if name.lower() in active_timers and not active_timers[name.lower()].done() else ""
        lines.append(f"• {name}: {state} {timer}")

    await update.message.reply_text("\n".join(lines))


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop <outlet_name> — turn off immediately and cancel timer."""
    if ALLOWED_USER_ID and update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /stop <plug_name>")
        return

    outlet_name = context.args[0]
    outlet = hub.get_outlet_by_name(outlet_name)
    if outlet is None:
        await update.message.reply_text(f"No outlet found named '{outlet_name}'")
        return

    # Cancel timer and turn off
    timer_key = outlet_name.lower()
    if timer_key in active_timers and not active_timers[timer_key].done():
        active_timers[timer_key].cancel()
        del active_timers[timer_key]

    outlet.set_on(outlet_on=False)
    await update.message.reply_text(f"🔴  {outlet_name} OFF")

async def battery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /battery command — report battery levels for all devices."""
    if ALLOWED_USER_ID and update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Unauthorized.")
        return

    raw_devices = hub.get("/devices")

    unique = {}
    for d in raw_devices:
        attr = d.get("attributes", {})
        batt = attr.get("batteryPercentage") or attr.get("batteryLevel")
        if batt is not None:
            uid = d.get("relationId") or d.get("id")
            if uid not in unique or d.get("room"):
                unique[uid] = d

    if not unique:
        await update.message.reply_text("No battery-powered devices found.")
        return

    grouped = {}
    for d in unique.values():
        dtype = d.get("deviceType", "Other")
        grouped.setdefault(dtype, []).append(d)

    lines = []
    for dtype, devices in sorted(grouped.items()):
        lines.append(f"\n<b>{dtype.upper()}</b>")
        for d in sorted(devices, key=lambda x: x.get("room", {}).get("name", "Unassigned")):
            attr = d.get("attributes", {})
            room = d.get("room", {}).get("name", "Unassigned") if d.get("room") else "Unassigned"
            name = attr.get("customName", "Unknown")
            batt = attr.get("batteryPercentage") or attr.get("batteryLevel")
            status = "OK 👍"
            if batt < 20: status = "LOW ⚠️"
            if batt < 10: status = "CRITICAL ‼️"
            lines.append(f"<code>{room} | {name} | {batt}% {status}</code>")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("go", go))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("battery", battery))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
