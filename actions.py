import os
import webbrowser
import random

try:
    from plyer import battery
    BATTERY_AVAILABLE = True
except Exception:
    BATTERY_AVAILABLE = False

try:
    from plyer import storagepath
    STORAGE_AVAILABLE = True
except Exception:
    STORAGE_AVAILABLE = False

try:
    from jnius import autoclass
    JNIUS_AVAILABLE = True
except Exception:
    JNIUS_AVAILABLE = False

APP_PACKAGES = {
    "whatsapp": "com.whatsapp",
    "instagram": "com.instagram.android",
    "tiktok": "com.zhiliaoapp.musically",
    "x": "com.twitter.android",
    "twitter": "com.twitter.android",
}


def quick_check(user_text):
    text = user_text.lower().strip()

    battery_words = ["battery", "charge left", "how much charge"]
    if any(word in text for word in battery_words):
        return check_battery()

    photo_words = ["how many photos", "photo count", "my gallery", "my pictures"]
    if any(word in text for word in photo_words):
        return list_photos()

    time_words = ["what time", "current time", "what's the time"]
    if any(word in text for word in time_words):
        return check_time()

    return None


def run_action(action_data):
    action = action_data.get("action", "none")

    if action == "check_battery":
        return check_battery()
    elif action == "check_wifi":
        return check_wifi()
    elif action == "open_url":
        return open_url(action_data.get("target", ""))
    elif action == "open_app":
        return open_app(action_data.get("target", ""))
    elif action == "list_photos":
        return list_photos()
    elif action == "show_photo":
        return get_random_photo_path()
    else:
        return None


def check_time():
    from datetime import datetime
    now = datetime.now().strftime("%I:%M %p")
    return f"It's currently {now}."


def check_battery():
    if not BATTERY_AVAILABLE:
        return "I can't check the battery on this device."
    try:
        status = battery.status
        percent = status.get("percentage", "unknown")
        charging = status.get("isCharging", False)
        state = "charging" if charging else "not charging"
        return f"Your battery is at {percent}% and {state}."
    except Exception as e:
        return f"Couldn't read battery info: {e}"


def check_wifi():
    return "Wifi status checking isn't fully supported on this device yet."


def open_url(target):
    if not target:
        return "I need a website or topic to open."
    url = target if target.startswith("http") else f"https://{target}"
    try:
        webbrowser.open(url)
        return f"Opening {target} for you."
    except Exception as e:
        return f"Couldn't open that: {e}"


def open_app(app_name):
    if not JNIUS_AVAILABLE:
        return "App launching isn't supported in this environment."

    app_name = app_name.lower().strip()
    package = APP_PACKAGES.get(app_name)

    if not package:
        return f"I don't have {app_name} mapped yet. Tell me its package name and I'll add it."

    try:
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        intent = context.getPackageManager().getLaunchIntentForPackage(package)
        if intent:
            context.startActivity(intent)
            return f"Opening {app_name}."
        else:
            return f"{app_name} doesn't seem to be installed. (package: {package})"
    except Exception as e:
        return f"Couldn't open {app_name}: {e}"


def _get_photo_folders():
    folders = []
    if STORAGE_AVAILABLE:
        try:
            folders.append(storagepath.get_pictures_dir())
        except Exception:
            pass
        try:
            folders.append(storagepath.get_dcim_dir())
        except Exception:
            pass
    return folders


def list_photos():
    folders = _get_photo_folders()
    if not folders:
        return "I can't access storage paths on this device."

    all_photos = []
    checked_paths = []

    for folder in folders:
        if folder and os.path.exists(folder):
            checked_paths.append(folder)
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith((".jpg", ".jpeg", ".png")):
                        all_photos.append(f)

    if not all_photos:
        return f"I didn't find any photos. Checked: {checked_paths}"

    count = len(all_photos)
    recent = all_photos[-3:]
    return f"You have {count} photos. Some recent ones: {', '.join(recent)}."


def get_random_photo_path():
    folders = _get_photo_folders()
    if not folders:
        return None

    all_paths = []
    for folder in folders:
        if folder and os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.lower().endswith((".jpg", ".jpeg", ".png")):
                        all_paths.append(os.path.join(root, f))

    if not all_paths:
        return None

    return random.choice(all_paths)
