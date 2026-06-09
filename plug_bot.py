import os
import re
import asyncio
from dotenv import load_dotenv
from dirigera import Hub
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3

# For plotting via /plot
import io, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timezone, timedelta

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
    matches = re.findall(r'(\d+)\s*(d|h|m|s)', text.lower())
    if not matches:
        return None
    for value, unit in matches:
        value = int(value)
        if unit == 'd':
            total += value * 60*60*24
        elif unit == 'h':
            total += value * 60*60
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
            status = "OK"
            if batt < 20: status = "LOW ⚠️"
            if batt < 10: status = "CRITICAL ‼️"
            lines.append(f"<code>{room:<12} | {name:<3} | {batt:>3}% {status}</code>")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

## Alert functionality
DB_PATH = os.getenv("READINGS_DB", "readings.db")
ALERT_THRESHOLDS = {"co2": 1000, "pm25": 15}

# Track rooms already alerted so we don't repeat
alerted: dict[str, float] = {}

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Periodic check of sensor readings against thresholds."""
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""
        SELECT room, reading_type, value
        FROM readings
        WHERE reading_type IN ('co2', 'pm25')
        AND timestamp = (
            SELECT MAX(timestamp) FROM readings
            WHERE reading_type IN ('co2', 'pm25')
        )
    """).fetchall()
    con.close()

    for room, rtype, value in rows:
        key = f"{room}:{rtype}"
        threshold = ALERT_THRESHOLDS[rtype]
        if value > threshold and key not in alerted:
            unit = "ppm" if rtype == "co2" else ""
            await context.bot.send_message(
                chat_id=ALLOWED_USER_ID,
                text=f"🚨 {room} — {rtype.upper()} is {value}{unit} (threshold: {threshold})"
            )
            alerted[key] = value
        elif value <= threshold and key in alerted:
            del alerted[key]

def group_rows(rows):
    "Group reading rows into {label: ([times],[vals])}"
    g = defaultdict(lambda: ([],[]))
    for ts,room,sensor,val in rows:
        t = datetime.fromisoformat(ts)
        g[f"{room} ({sensor})"][0].append(t)
        g[f"{room} ({sensor})"][1].append(val)
    return g

def make_plot(rows, rtype, dur):
    "Render readings to an in-memory PNG buffer"
    g = group_rows(rows)
    fig,ax = plt.subplots(figsize=(8,4))
    for label,(ts,vals) in g.items(): ax.plot(ts, vals, marker='.', label=label)
    ax.set_title(f"{rtype} (last {dur})"); ax.set_xlabel("time"); ax.set_ylabel(rtype); ax.legend(fontsize=7)
    fig.autofmt_xdate(); fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=100); buf.seek(0); plt.close(fig)
    return buf

async def plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    "Handle /plot <reading_type> <duration> command."
    if ALLOWED_USER_ID and update.effective_user.id != ALLOWED_USER_ID: return await update.message.reply_text("Unauthorized.")
    args = context.args
    if len(args) < 2: return await update.message.reply_text("Usage: /plot <reading_type> <duration>\nExample: /plot pm25 6h")
    rtype,dur = args[0],args[1]
    seconds = parse_duration(dur)
    if seconds is None: return await update.message.reply_text(f"Couldn't parse duration: '{dur}'")
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("SELECT timestamp,room,sensor,value FROM readings WHERE reading_type=? AND timestamp>=? ORDER BY timestamp ASC", (rtype,cutoff)).fetchall()
    con.close()
    if not rows: return await update.message.reply_text(f"No {rtype} readings in last {dur}")
    await update.message.reply_photo(make_plot(rows, rtype, dur))

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("go", go))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("battery", battery))
    app.add_handler(CommandHandler("plot", plot))

    job_queue = app.job_queue
    job_queue.run_repeating(check_alerts, interval=900, first=900)

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
