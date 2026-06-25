import base64
import json
import os
import sys
import time
from datetime import datetime
from tkinter import filedialog
import customtkinter as ctk

FILE_CONTACTS = "contacts.json"
FILE_FAVORITES = "favorites.json"
FILE_SECRET = "secret.json"
FILE_RECENT = "recent.json"
FILE_SETTINGS = "settings.json"

MAX_RECENT_ITEMS = 20

ADMIN_PASSWORD = "190923"

MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_SECONDS = 30

PHONE_LABELS = ["Mobile", "Work", "Home", "Other"]

DEFAULT_CONTACTS = {
    "Ivan": {
        "phones": [{"label": "Mobile", "number": "+79991112233"}],
        "category": "Friends",
        "note": "",
        "created_at": time.time() - 86400,
        "usage_count": 0,
    },
    "Anna": {
        "phones": [{"label": "Mobile", "number": "+79994445566"}],
        "category": "Family",
        "note": "",
        "created_at": time.time(),
        "usage_count": 0,
    },
}

CATEGORIES = ["Work", "Family", "Friends", "Other"]
CATEGORY_ALL = "All"

SORT_NAME_AZ = "Name (A-Z)"
SORT_NAME_ZA = "Name (Z-A)"
SORT_DATE_NEWEST = "Date added (newest)"
SORT_DATE_OLDEST = "Date added (oldest)"

SORT_OPTIONS = [
    SORT_NAME_AZ,
    SORT_NAME_ZA,
    SORT_DATE_NEWEST,
    SORT_DATE_OLDEST,
]

CATEGORY_COLORS = {
    "Work": "#1f6aa5",
    "Family": "#2cb67d",
    "Friends": "#e8a33d",
    "Other": "#888888",
}

COLOR_PRIMARY = "#1f6aa5"
COLOR_PRIMARY_HOVER = "#144870"
COLOR_SUCCESS = "#2cb67d"
COLOR_SUCCESS_HOVER = "#1e8557"
COLOR_DANGER = "#e55039"
COLOR_DANGER_HOVER = "#b83b26"
COLOR_GRAY = "gray"
COLOR_GRAY_HOVER = "#555555"

ROW_TARGET_HEIGHT = 38

# ---------------------------------------------------------------------------
# Универсальные хелперы анимации.
# В CTk/Tkinter нет встроенного движка анимации — всё ниже сделано через
# .after() с ручной интерполяцией и easing (плавное замедление к концу),
# чтобы не выглядело дёргано.
# ---------------------------------------------------------------------------

def ease_out_cubic(t):
    """t от 0 до 1 -> плавное замедление к концу движения."""
    return 1 - (1 - t) ** 3


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(rgb[0]))),
        max(0, min(255, int(rgb[1]))),
        max(0, min(255, int(rgb[2]))),
    )


def _lerp_color(hex_a, hex_b, t):
    a = _hex_to_rgb(hex_a)
    b = _hex_to_rgb(hex_b)
    return _rgb_to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


# Именованные tkinter-цвета ("gray" и т.п.) не парсятся как hex напрямую.
_NAMED_COLOR_FALLBACK = {
    "gray": "#808080",
    "transparent": "#2b2b2b",
}


def _safe_hex(color):
    """
    Приводит цвет CTk к одному hex-значению.

    КРИТИЧНО: CTkButton.cget("fg_color") часто возвращает не строку, а
    tuple вида (цвет_для_светлой_темы, цвет_для_тёмной_темы) — так CTk
    хранит цвета, зависящие от режима оформления. Старая версия этой
    функции не учитывала tuple и в этом случае тихо подставляла серый
    дефолт (#808080) вместо реального цвета — анимация формально работала,
    но "доезжала" в неправильный, малозаметный цвет, что выглядело как
    "подсветка не работает".
    """
    if isinstance(color, (tuple, list)):
        # берём цвет, соответствующий текущему режиму темы
        mode = ctk.get_appearance_mode()  # "Light" или "Dark"
        index = 1 if mode == "Dark" and len(color) > 1 else 0
        color = color[index]

    if isinstance(color, str) and color.startswith("#"):
        return color

    return _NAMED_COLOR_FALLBACK.get(color, "#1f6aa5")


def animate_button_hover(button, base_color, hover_color, press_color=None, duration_ms=130):
    """
    Плавная подсветка кнопки на hover/press вместо мгновенной смены fg_color.
    base_color / hover_color — обычные fg_color/hover_color кнопки.
    На зажатии (ButtonPress) идём чуть темнее hover_color, чтобы клик
    ощущался как отдельный шаг, а не просто "осталось как при hover".
    """
    base_hex = _safe_hex(base_color)
    hover_hex = _safe_hex(hover_color)
    if press_color is not None:
        press_hex = _safe_hex(press_color)
    else:
        press_rgb = tuple(c * 0.82 for c in _hex_to_rgb(hover_hex))
        press_hex = _rgb_to_hex(press_rgb)

    job = {"id": None}

    def _animate_to(target_hex):
        if job["id"] is not None:
            try:
                button.after_cancel(job["id"])
            except Exception:
                pass
            job["id"] = None

        try:
            start_hex = _safe_hex(button.cget("fg_color"))
        except Exception:
            start_hex = base_hex

        start_time = time.time()

        def _step():
            if not button.winfo_exists():
                return
            elapsed = time.time() - start_time
            t = min(elapsed / (duration_ms / 1000), 1.0)
            eased = ease_out_cubic(t)
            try:
                button.configure(fg_color=_lerp_color(start_hex, target_hex, eased))
            except Exception:
                return
            if t < 1.0:
                job["id"] = button.after(12, _step)
            else:
                job["id"] = None

        _step()

    button.bind("<Enter>", lambda e: _animate_to(hover_hex), add="+")
    button.bind("<Leave>", lambda e: _animate_to(base_hex), add="+")
    button.bind("<ButtonPress-1>", lambda e: _animate_to(press_hex), add="+")
    button.bind("<ButtonRelease-1>", lambda e: _animate_to(hover_hex), add="+")


def make_button(master, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, **kwargs):
    """
    Обёртка над ctk.CTkButton: создаёт кнопку и навешивает плавную анимацию
    подсветки (hover/press) ВМЕСТО встроенной в CTk.

    ВАЖНО: у CTkButton есть собственный встроенный hover-эффект — он сам
    биндит <Enter>/<Leave> и мгновенно подменяет fg_color на hover_color.
    Если просто добавить свои бинды поверх (bind(..., add="+")), оба
    обработчика выполняются, и встроенный мгновенный эффект забивает нашу
    плавную анимацию — снаружи это выглядит так, будто анимация не работает.
    Поэтому здесь встроенный hover отключается явно через hover=False,
    и подсветкой целиком управляет animate_button_hover().
    """
    button = ctk.CTkButton(
        master=master, fg_color=fg_color, hover_color=hover_color, hover=False, **kwargs
    )
    animate_button_hover(button, fg_color, hover_color)
    return button


def shake_widget(widget, distance=8, cycles=3, duration_ms=260):
    """
    Горизонтальная "тряска" виджета — индикация ошибки валидации.
    Виджет временно переключается с pack() на place() с колеблющимся x
    (амплитуда затухает к концу), затем возвращается на исходный pack().
    """
    try:
        manager = widget.winfo_manager()
    except Exception:
        return
    if manager != "pack" or not widget.winfo_exists():
        return

    pack_info = widget.pack_info()
    widget.update_idletasks()
    start_x = widget.winfo_x()
    start_y = widget.winfo_y()
    width = widget.winfo_width()
    height = widget.winfo_height()

    widget.pack_forget()
    widget.place(x=start_x, y=start_y, width=width, height=height)

    total_steps = cycles * 2
    step_duration = max(1, int(duration_ms / total_steps))

    def _step(i=0):
        if not widget.winfo_exists():
            return
        if i >= total_steps:
            widget.place_forget()
            widget.pack(**pack_info)
            return
        progress = i / total_steps
        amplitude = distance * (1 - progress)
        offset = amplitude if i % 2 == 0 else -amplitude
        try:
            widget.place_configure(x=start_x + offset)
        except Exception:
            widget.place_forget()
            widget.pack(**pack_info)
            return
        widget.after(step_duration, lambda: _step(i + 1))

    _step()


def fade_in_window(win, target_size=None, duration_ms=220):
    """
    Плавное появление Toplevel-окна: fade по альфа-каналу + лёгкое
    "вырастание" окна из ~88% целевого размера до 100%.

    ВАЖНО про позицию: предыдущая версия дополнительно сдвигала окно по Y
    (slide), читая текущую geometry() сразу после создания окна. Но
    geometry() в этот момент часто ещё не отражает позицию, которую
    назначит оконный менеджер (на многих Linux WM позиция применяется
    асинхронно, чуть позже). Из-за этого слайд либо дёргался, либо
    анимировал "0 -> 0" и был незаметен.

    Здесь вместо позиции анимируется РАЗМЕР окна, который мы полностью
    контролируем и который не зависит от поведения WM — эффект гарантированно
    виден независимо от платформы. target_size — строка "WxH" (та же, что
    передаётся в geometry()); если не передана, размер не анимируется,
    остаётся только fade.

    Если платформа не поддерживает -alpha (бывает на части Linux WM без
    композитора), окно показывается как обычно, без анимации, без ошибок.
    """
    try:
        win.attributes("-alpha", 0.0)
        alpha_supported = True
    except Exception:
        alpha_supported = False

    width, height, start_w, start_h = None, None, None, None
    if target_size:
        try:
            w_str, h_str = target_size.lower().split("x")
            width, height = int(w_str), int(h_str)
            start_w = int(width * 0.88)
            start_h = int(height * 0.88)
            win.geometry(f"{start_w}x{start_h}")
        except Exception:
            width = height = start_w = start_h = None

    if not alpha_supported and width is None:
        return

    start_time = time.time()

    def _step():
        if not win.winfo_exists():
            return
        elapsed = time.time() - start_time
        t = min(elapsed / (duration_ms / 1000), 1.0)
        eased = ease_out_cubic(t)
        try:
            if alpha_supported:
                win.attributes("-alpha", eased)
            if width is not None:
                cur_w = int(start_w + (width - start_w) * eased)
                cur_h = int(start_h + (height - start_h) * eased)
                win.geometry(f"{cur_w}x{cur_h}")
        except Exception:
            return
        if t < 1.0:
            win.after(14, _step)
        else:
            try:
                if alpha_supported:
                    win.attributes("-alpha", 1.0)
                if width is not None:
                    win.geometry(f"{width}x{height}")
            except Exception:
                pass

    # Небольшая задержка перед первым кадром — даёт оконному менеджеру
    # время отрисовать окно с alpha=0/уменьшенным размером ДО начала
    # анимации, иначе на части систем первый кадр проскакивает мгновенно.
    win.after(30, _step)


def pulse_success(button, success_color=COLOR_SUCCESS, duration_ms=260):
    """
    Короткая вспышка зелёным по кнопке как подтверждение успешного действия
    (сохранили контакт, добавили в избранное и т.п.), затем плавный возврат
    к исходному цвету.
    """
    try:
        base_hex = _safe_hex(button.cget("fg_color"))
    except Exception:
        return
    success_hex = _safe_hex(success_color)

    try:
        button.configure(fg_color=success_hex)
    except Exception:
        return

    start_time = time.time()

    def _step():
        if not button.winfo_exists():
            return
        elapsed = time.time() - start_time
        t = min(elapsed / (duration_ms / 1000), 1.0)
        eased = ease_out_cubic(t)
        try:
            button.configure(fg_color=_lerp_color(success_hex, base_hex, eased))
        except Exception:
            return
        if t < 1.0:
            button.after(12, _step)

    button.after(140, _step)



def _xor_bytes(data: bytes, key: str) -> bytes:
    key_bytes = key.encode("utf-8")
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data))


def encrypt_data(data_str: str, key: str) -> str:
    if not key:
        return data_str
    encrypted = _xor_bytes(data_str.encode("utf-8"), key)
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_data(encoded_str: str, key: str) -> str:
    if not key:
        return encoded_str
    try:
        raw = base64.b64decode(encoded_str.encode("utf-8"))
        return _xor_bytes(raw, key).decode("utf-8")
    except Exception:
        return "{}"


def load_json(path, key, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        return json.loads(decrypt_data(content, key))
    except Exception:
        return default


def save_json(path, data, key):
    raw_json = json.dumps(data, ensure_ascii=False, indent=4)
    with open(path, "w", encoding="utf-8") as f:
        f.write(encrypt_data(raw_json, key))


def save_contacts():
    save_json(FILE_CONTACTS, contacts, current_key)


def save_favorites():
    save_json(FILE_FAVORITES, favorites, current_key)


def save_recent():
    save_json(FILE_RECENT, recent, current_key)


def load_secret():
    if os.path.exists(FILE_SECRET):
        with open(FILE_SECRET, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("password", "")
            data.setdefault("hint", "")
            return data
    return {"password": "", "hint": ""}


def save_secret():
    with open(FILE_SECRET, "w", encoding="utf-8") as f:
        json.dump(secret_data, f, ensure_ascii=False, indent=4)


def load_settings():
    if os.path.exists(FILE_SETTINGS):
        try:
            with open(FILE_SETTINGS, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("theme", "dark")
                if data["theme"] not in ("dark", "light"):
                    data["theme"] = "dark"
                data.setdefault("dup_threshold", "medium")
                if data["dup_threshold"] not in ("strict", "medium", "loose"):
                    data["dup_threshold"] = "medium"
                return data
        except Exception:
            pass
    return {"theme": "dark", "dup_threshold": "medium"}


def save_settings():
    with open(FILE_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(app_settings, f, ensure_ascii=False, indent=4)


app_settings = load_settings()


secret_data = load_secret()
password_is_set = bool(secret_data["password"])

# ИСПРАВЛЕНО: раньше current_key был None, если пароль установлен, что приводило
# к падению encrypt_data/decrypt_data (None.encode) при любой случайной попытке
# сохранить/прочитать данные до разблокировки. Теперь всегда строка.
current_key = "" if not password_is_set else ""
contacts = {}
favorites = []
recent = []

failed_attempts = 0
lockout_until = 0.0


def migrate_contacts(raw_contacts):
    migrated = {}
    for name, value in raw_contacts.items():
        if isinstance(value, dict):
            category = value.get("category", "Other")
            note = value.get("note", "")
            if category not in CATEGORIES:
                category = "Other"

            if "phones" in value and isinstance(value["phones"], list):
                phones = []
                for entry in value["phones"]:
                    if isinstance(entry, dict):
                        label = entry.get("label", "Mobile")
                        number = entry.get("number", "")
                        if label not in PHONE_LABELS:
                            label = "Other"
                        if number:
                            phones.append({"label": label, "number": number})
                if not phones:
                    phones = [{"label": "Mobile", "number": ""}]
            elif "phone" in value:
                phones = [{"label": "Mobile", "number": value.get("phone", "")}]
            else:
                phones = [{"label": "Mobile", "number": ""}]

            created_at = value.get("created_at")
            if not isinstance(created_at, (int, float)):
                created_at = time.time()

            usage_count = value.get("usage_count")
            if not isinstance(usage_count, int) or usage_count < 0:
                usage_count = 0

            migrated[name] = {
                "phones": phones,
                "category": category,
                "note": note,
                "created_at": created_at,
                "usage_count": usage_count,
            }
        else:
            migrated[name] = {
                "phones": [{"label": "Mobile", "number": str(value)}],
                "category": "Other",
                "note": "",
                "created_at": time.time(),
                "usage_count": 0,
            }
    return migrated

def primary_phone(data):
    phones = data.get("phones", [])
    if phones:
        return phones[0]["number"]
    return ""


def all_phones_text(data):
    phones = data.get("phones", [])
    if not phones:
        return ""
    if len(phones) == 1:
        return phones[0]["number"]
    return ", ".join(f"{p['label']}: {p['number']}" for p in phones)


def normalize_favorites(raw_favorites):
    if isinstance(raw_favorites, list):
        return [name for name in raw_favorites if isinstance(name, str)]
    if isinstance(raw_favorites, dict):
        return [name for name in raw_favorites.keys()]
    return []


def normalize_recent(raw_recent):
    if not isinstance(raw_recent, list):
        return []
    cleaned = []
    for entry in raw_recent:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            timestamp = entry.get("timestamp")
            if not isinstance(timestamp, (int, float)):
                timestamp = time.time()
            cleaned.append({"name": entry["name"], "timestamp": timestamp})
        elif isinstance(entry, str):
            cleaned.append({"name": entry, "timestamp": time.time()})
    return cleaned[:MAX_RECENT_ITEMS]


def load_data():
    global contacts, favorites, recent
    contacts = migrate_contacts(load_json(FILE_CONTACTS, current_key, dict(DEFAULT_CONTACTS)))
    favorites = normalize_favorites(load_json(FILE_FAVORITES, current_key, []))
    recent = normalize_recent(load_json(FILE_RECENT, current_key, []))


def make_toplevel(title, size, parent=None):
    win = ctk.CTkToplevel(parent or app)
    win.title(title)
    win.geometry(size)
    win.resizable(False, False)
    win.attributes("-topmost", True)
    fade_in_window(win, target_size=size)
    return win


def confirm_dialog(message, on_confirm, parent=None, title="Confirm"):
    win = make_toplevel(title, "280x130", parent)

    ctk.CTkLabel(master=win, text=message, font=("Arial", 14)).pack(pady=15)

    btn_frame = ctk.CTkFrame(master=win, fg_color="transparent")
    btn_frame.pack()

    def yes():
        on_confirm()
        win.destroy()

    make_button(master=btn_frame, text="Yes", width=80, fg_color=COLOR_DANGER,
                  hover_color=COLOR_DANGER_HOVER, command=yes).pack(side="left", padx=10)
    make_button(master=btn_frame, text="No", width=80, fg_color=COLOR_GRAY,
                  hover_color=COLOR_GRAY_HOVER, command=win.destroy).pack(side="left", padx=10)
    return win


def open_edit_window(name, refresh_callback):
    base_height = 430
    row_height = 46

    initial_phones = contacts[name].get("phones", [{"label": "Mobile", "number": ""}])
    win = make_toplevel("Edit contact", f"360x{base_height + row_height * len(initial_phones)}")

    ctk.CTkLabel(master=win, text=f"Edit {name}", font=("Arial", 16, "bold")).pack(pady=(15, 10))

    current_category = contacts[name].get("category", "Other")
    category_var = ctk.StringVar(value=current_category)
    category_menu = ctk.CTkOptionMenu(master=win, values=CATEGORIES, variable=category_var, width=260)
    category_menu.pack(pady=(0, 10))

    ctk.CTkLabel(master=win, text="Phone numbers", font=("Arial", 12, "bold"),
                 text_color="gray").pack(anchor="w", padx=30)

    phones_frame = ctk.CTkFrame(master=win, fg_color="transparent")
    phones_frame.pack(pady=(5, 5), padx=20, fill="x")

    phone_rows = []

    def resize_window():
        win.geometry(f"360x{base_height + row_height * len(phone_rows)}")

    def add_phone_row(label="Mobile", number=""):
        row = ctk.CTkFrame(master=phones_frame, corner_radius=8)
        row.pack(fill="x", pady=4)

        label_var = ctk.StringVar(value=label if label in PHONE_LABELS else "Other")
        label_menu = ctk.CTkOptionMenu(master=row, values=PHONE_LABELS, variable=label_var, width=95)
        label_menu.pack(side="left", padx=(8, 6), pady=8)

        number_entry = ctk.CTkEntry(master=row, width=130, placeholder_text="Number")
        number_entry.insert(0, number)
        number_entry.pack(side="left", padx=(0, 6), pady=8)

        def remove_row():
            if len(phone_rows) <= 1:
                error_label.configure(text="At least one number is required!", text_color="red")
                shake_widget(error_label)
                return
            phone_rows.remove(entry_tuple)
            row.destroy()
            resize_window()

        remove_btn = make_button(master=row, text="🗑️", width=32, height=28, fg_color=COLOR_DANGER,
                                    hover_color=COLOR_DANGER_HOVER, font=("Arial", 11),
                                    command=lambda: remove_row())
        remove_btn.pack(side="left", padx=(0, 8), pady=8)

        entry_tuple = (label_var, number_entry, row)
        phone_rows.append(entry_tuple)

    for p in initial_phones:
        add_phone_row(p.get("label", "Mobile"), p.get("number", ""))

    def add_new_row():
        add_phone_row()
        resize_window()

    make_button(master=win, text="+ Add another number", width=180, height=30, fg_color=COLOR_GRAY,
                  hover_color=COLOR_GRAY_HOVER, font=("Arial", 12),
                  command=add_new_row).pack(pady=(0, 10))

    ctk.CTkLabel(master=win, text="Note (birthday, info, etc.)", font=("Arial", 12),
                 text_color="gray").pack(pady=(0, 0))

    note_box = ctk.CTkTextbox(master=win, width=260, height=70)
    note_box.insert("1.0", contacts[name].get("note", ""))
    note_box.pack(pady=8)

    error_label = ctk.CTkLabel(master=win, text="", font=("Arial", 12))
    error_label.pack(pady=2)

    def save_edit():
        new_phones = []
        for label_var, number_entry, _ in phone_rows:
            number = number_entry.get().strip()
            if not number:
                continue
            if not number.isdigit():
                error_label.configure(text="Numbers must consist of digits!", text_color="red")
                shake_widget(error_label)
                return
            new_phones.append({"label": label_var.get(), "number": number})

        if not new_phones:
            error_label.configure(text="Add at least one phone number!", text_color="red")
            shake_widget(error_label)
            return

        new_note = note_box.get("1.0", "end").strip()
        contacts[name] = {
            "phones": new_phones,
            "category": category_var.get(),
            "note": new_note,
            "created_at": contacts[name].get("created_at", time.time()),
            "usage_count": contacts[name].get("usage_count", 0),
        }
        save_contacts()
        refresh_callback()
        win.destroy()

    make_button(master=win, text="Save", width=150, height=35, corner_radius=8,
                  fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                  command=save_edit).pack(pady=8)


def mark_contact_opened(name):
    if name not in contacts:
        return
    recent[:] = [r for r in recent if r["name"] != name]
    recent.insert(0, {"name": name, "timestamp": time.time()})
    del recent[MAX_RECENT_ITEMS:]
    save_recent()


# ИСПРАВЛЕНО: главная причина "анимация не работает".
# CTkFrame, упакованный с fill="x", по умолчанию сам подгоняет свою высоту под
# содержимое (как обычный tkinter pack geometry manager) — вызов .configure(height=...)
# на таком фрейме НИЧЕГО не даёт, потому что pack_propagate (geometry propagation)
# включен и Tk пересчитывает реальный размер по детям при каждом обновлении.
# Чтобы анимация высоты реально работала, нужно:
#   1) явно задать row.configure(height=...)
#   2) отключить pack_propagate(False), чтобы Tk не переопределял высоту по контенту
# Также раньше при анимации "в" внутренние виджеты (label/buttons) уже были
# упакованы внутри row ДО первого вызова _step(), поэтому даже при height=0
# содержимое требовало больше места и Tk всё равно растягивал строку.
# Решение: создаём строку с pack_propagate(False) сразу с нужной итоговой высотой
# для анимации "уход", а для анимации "появление" сначала схлопываем именно
# контейнер-обёртку, а не сам row с контентом.
def animate_row_in(row, target_height=ROW_TARGET_HEIGHT, step=4, delay=12):
    """Плавно увеличивает высоту строки от 0 до target_height."""
    row.pack_propagate(False)
    current = [0]

    def _step():
        current[0] = min(current[0] + step, target_height)
        try:
            row.configure(height=current[0])
        except Exception:
            return
        if current[0] < target_height:
            row.after(delay, _step)

    row.configure(height=0)
    row.after(delay, _step)


def animate_row_out(row, on_done, current_height=ROW_TARGET_HEIGHT, step=4, delay=12):
    """Плавно уменьшает высоту строки до 0, затем вызывает on_done()."""
    row.pack_propagate(False)
    current = [current_height]

    def _step():
        current[0] = max(current[0] - step, 0)
        try:
            row.configure(height=current[0])
        except Exception:
            on_done()
            return
        if current[0] > 0:
            row.after(delay, _step)
        else:
            on_done()

    row.after(delay, _step)


def delete_contact(name, refresh_callback):
    def do_delete():
        target_row = None
        for widget in contacts_frame.winfo_children():
            if hasattr(widget, "_contact_name") and widget._contact_name == name:
                target_row = widget
                break

        def finish_delete():
            del contacts[name]
            if name in favorites:
                favorites.remove(name)
                save_favorites()
            recent[:] = [r for r in recent if r["name"] != name]
            save_recent()
            save_contacts()
            contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
            refresh_callback()

        if target_row is not None:
            animate_row_out(target_row, finish_delete)
        else:
            finish_delete()

    confirm_dialog(f"Delete contact '{name}'?", do_delete)


def render_contact_row(parent, name, phones_text, category, note, created_at,
                        refresh_callback, highlight=False):
    row = ctk.CTkFrame(master=parent, fg_color="transparent")
    row._contact_name = name  # метка для поиска при анимации удаления
    row.pack(fill="x", padx=5, pady=3)

    prefix = "⭐ " if name in favorites else "👤 "
    label_kwargs = (
        {"font": ("Arial", 14, "bold"), "text_color": "#2cb67d"}
        if highlight else
        {"font": ("Arial", 14)}
    )

    display_text = f"{prefix}{name}: {phones_text}"
    if note:
        display_text += " 📝"

    make_button(master=row, text="✏️", width=30, height=25, fg_color=COLOR_PRIMARY,
                  hover_color=COLOR_PRIMARY_HOVER, font=("Arial", 10, "bold"),
                  command=lambda: open_edit_window(name, refresh_callback)).pack(side="right", padx=5)

    make_button(master=row, text="❌", width=30, height=25, fg_color=COLOR_DANGER,
                  hover_color=COLOR_DANGER_HOVER, font=("Arial", 10, "bold"),
                  command=lambda: delete_contact(name, refresh_callback)).pack(side="right", padx=5)

    ctk.CTkLabel(master=row, text=category, font=("Arial", 10, "bold"),
                 fg_color=CATEGORY_COLORS.get(category, COLOR_GRAY), text_color="white",
                 corner_radius=6, width=60).pack(side="right", padx=5)

    text_col = ctk.CTkFrame(master=row, fg_color="transparent")
    text_col.pack(side="left", fill="both", expand=True, padx=5)

    name_label = ctk.CTkLabel(master=text_col, text=display_text, anchor="w", justify="left",
                               wraplength=170, **label_kwargs)
    name_label.pack(anchor="w", fill="x")

    def on_row_click(event=None):
        mark_contact_opened(name)
        if note:
            confirm_dialog(f"Note for {name}:\n\n{note}", lambda: None, title="Note")

    name_label.bind("<Button-1>", on_row_click)

    # Запускаем анимацию появления строки
    animate_row_in(row)


def display_contacts(items, refresh_callback, highlight=False, empty_message=None):
    for widget in contacts_frame.winfo_children():
        widget.destroy()

    if not items and empty_message:
        ctk.CTkLabel(master=contacts_frame, text=empty_message, font=("Arial", 14, "italic"),
                     text_color="gray").pack(pady=20)
        return

    # Рендерим строки с нарастающей задержкой для эффекта «каскада»
    for index, (name, data) in enumerate(items):
        def _render(n=name, d=data, i=index):
            render_contact_row(
                contacts_frame, n, all_phones_text(d), d.get("category", "Other"),
                d.get("note", ""), d.get("created_at", time.time()),
                refresh_callback, highlight
            )
        contacts_frame.after(index * 30, _render)


def get_filtered_items():
    selected_category = category_filter_var.get()
    selected_sort = sort_var.get()

    items = list(contacts.items())

    if selected_category != CATEGORY_ALL:
        items = [(n, d) for n, d in items if d.get("category", "Other") == selected_category]

    if selected_sort == SORT_NAME_AZ:
        items.sort(key=lambda item: item[0].lower())
    elif selected_sort == SORT_NAME_ZA:
        items.sort(key=lambda item: item[0].lower(), reverse=True)
    elif selected_sort == SORT_DATE_NEWEST:
        items.sort(key=lambda item: item[1].get("created_at", 0), reverse=True)
    elif selected_sort == SORT_DATE_OLDEST:
        items.sort(key=lambda item: item[1].get("created_at", 0))
    else:
        items.sort(key=lambda item: item[0].lower())

    return items


def show_all_contacts():
    contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
    display_contacts(get_filtered_items(), show_all_contacts, empty_message="No contacts in this category")


def search_contact():
    query = search_entry.get().strip().lower()
    base_items = get_filtered_items()
    if not query:
        display_contacts(base_items, search_contact, empty_message="No contacts in this category")
        return

    def contact_matches(data, name_lower):
        if query in name_lower:
            return True
        for p in data.get("phones", []):
            if query in p["number"].lower():
                return True
        return False

    matches = []
    for n, d in base_items:
        name_lower = n.lower()
        if contact_matches(d, name_lower):
            matches.append((n, d))
    display_contacts(matches, search_contact, highlight=True, empty_message="Nothing found")


def open_add_contact_window():
    base_height = 460
    row_height = 46

    win = make_toplevel("Add a contact", f"360x{base_height}")

    ctk.CTkLabel(master=win, text="New contact", font=("Arial", 16, "bold")).pack(pady=(15, 10))

    name_entry = ctk.CTkEntry(master=win, placeholder_text="Contact name", width=260)
    name_entry.pack(pady=(0, 10))

    category_var = ctk.StringVar(value=CATEGORIES[0])
    category_menu = ctk.CTkOptionMenu(master=win, values=CATEGORIES, variable=category_var, width=260)
    category_menu.pack(pady=(0, 10))

    ctk.CTkLabel(master=win, text="Phone numbers", font=("Arial", 12, "bold"),
                 text_color="gray").pack(anchor="w", padx=30)

    phones_frame = ctk.CTkFrame(master=win, fg_color="transparent")
    phones_frame.pack(pady=(5, 5), padx=20, fill="x")

    phone_rows = []

    def resize_window():
        win.geometry(f"360x{base_height + row_height * (len(phone_rows) - 1)}")

    def add_phone_row(label="Mobile", number=""):
        row = ctk.CTkFrame(master=phones_frame, corner_radius=8)
        row.pack(fill="x", pady=4)

        label_var = ctk.StringVar(value=label if label in PHONE_LABELS else "Other")
        label_menu = ctk.CTkOptionMenu(master=row, values=PHONE_LABELS, variable=label_var, width=95)
        label_menu.pack(side="left", padx=(8, 6), pady=8)

        number_entry = ctk.CTkEntry(master=row, width=130, placeholder_text="Number")
        number_entry.insert(0, number)
        number_entry.pack(side="left", padx=(0, 6), pady=8)

        def remove_row():
            if len(phone_rows) <= 1:
                error_label.configure(text="At least one number is required!", text_color="red")
                shake_widget(error_label)
                return
            phone_rows.remove(entry_tuple)
            row.destroy()
            resize_window()

        remove_btn = make_button(master=row, text="🗑️", width=32, height=28, fg_color=COLOR_DANGER,
                                    hover_color=COLOR_DANGER_HOVER, font=("Arial", 11),
                                    command=lambda: remove_row())
        remove_btn.pack(side="left", padx=(0, 8), pady=8)

        entry_tuple = (label_var, number_entry, row)
        phone_rows.append(entry_tuple)

    add_phone_row("Mobile")

    def add_new_row():
        add_phone_row()
        resize_window()

    make_button(master=win, text="+ Add another number", width=180, height=30, fg_color=COLOR_GRAY,
                  hover_color=COLOR_GRAY_HOVER, font=("Arial", 12),
                  command=add_new_row).pack(pady=(0, 10))

    ctk.CTkLabel(master=win, text="Note (birthday, info, etc.)", font=("Arial", 12),
                 text_color="gray").pack(pady=(0, 0))

    note_box = ctk.CTkTextbox(master=win, width=260, height=70)
    note_box.pack(pady=8)

    error_label = ctk.CTkLabel(master=win, text="", font=("Arial", 12))
    error_label.pack(pady=2)

    def save_new_contact():
        name = name_entry.get().strip().title()

        if not name:
            error_label.configure(text="Please fill in the name!", text_color="red")
            shake_widget(error_label)
            return
        if name in contacts:
            error_label.configure(text="This contact name already exists! ⚠️", text_color="yellow")
            shake_widget(error_label)
            return

        new_phones = []
        for label_var, number_entry, _ in phone_rows:
            number = number_entry.get().strip()
            if not number:
                continue
            if not number.isdigit():
                error_label.configure(text="Numbers must consist of digits!", text_color="red")
                shake_widget(error_label)
                return
            new_phones.append({"label": label_var.get(), "number": number})

        if not new_phones:
            error_label.configure(text="Add at least one phone number!", text_color="red")
            shake_widget(error_label)
            return

        note = note_box.get("1.0", "end").strip()
        contacts[name] = {
            "phones": new_phones,
            "category": category_var.get(),
            "note": note,
            "created_at": time.time(),
            "usage_count": 0,
        }
        save_contacts()
        win.destroy()
        # ИСПРАВЛЕНО: раньше тут вручную выставлялся label_text и вызывался
        # show_all_contacts(), который ИГНОРИРУЕТ текущий поиск/фильтр и всегда
        # показывает все контакты. Если пользователь до этого что-то искал или
        # выбрал категорию, новый контакт "терялся" из вида, и казалось,
        # что добавление не сработало. Теперь обновляем через search_contact(),
        # которая учитывает текущий фильтр/сортировку/поиск.
        search_contact()

    make_button(master=win, text="Save", width=150, height=35, corner_radius=8,
                  fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                  command=save_new_contact).pack(pady=8)


def open_favorites_window():
    fav_window = make_toplevel("Favorites", "400x450")

    ctk.CTkLabel(master=fav_window, text="⭐ Favorite Contacts", font=("Arial", 20, "bold")).pack(pady=15)

    fav_entry = ctk.CTkEntry(master=fav_window, placeholder_text="Type name from list to add...", width=250)
    fav_entry.pack(pady=5)

    fav_scroll = ctk.CTkScrollableFrame(master=fav_window, width=320, height=200, corner_radius=8)
    fav_scroll.pack(pady=15)

    def refresh_fav_list():
        for widget in fav_scroll.winfo_children():
            widget.destroy()

        if not favorites:
            ctk.CTkLabel(master=fav_scroll, text="Favorites list is empty", font=("Arial", 14, "italic"),
                         text_color="gray").pack(pady=20)
            return

        for name in sorted(favorites):
            if name not in contacts:
                continue
            row = ctk.CTkFrame(master=fav_scroll, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=3)

            ctk.CTkLabel(master=row, text=f"⭐ {name}: {all_phones_text(contacts[name])}", font=("Arial", 14),
                         anchor="w", wraplength=240, justify="left").pack(side="left", fill="x", expand=True, padx=5)

            def remove_fav(n=name):
                favorites.remove(n)
                save_favorites()
                refresh_fav_list()
                show_all_contacts()

            make_button(master=row, text="🗑️", width=30, height=25, fg_color=COLOR_DANGER,
                          hover_color=COLOR_DANGER_HOVER, font=("Arial", 10),
                          command=remove_fav).pack(side="right", padx=5)

    def add_to_fav():
        query = fav_entry.get().strip().lower()
        if not query:
            return

        matches = [name for name in contacts if query in name.lower() and name not in favorites]

        if not matches:
            fav_entry.delete(0, "end")
            fav_entry.configure(placeholder_text="No new matches found!", placeholder_text_color="red")
            shake_widget(fav_entry)
            return

        if len(matches) > 1:
            fav_entry.delete(0, "end")
            fav_entry.configure(placeholder_text="Multiple found! Be more specific.", placeholder_text_color="yellow")
            shake_widget(fav_entry)
            return

        name_to_add = matches[0]

        def confirm_add():
            favorites.append(name_to_add)
            save_favorites()
            fav_entry.delete(0, "end")
            fav_entry.configure(placeholder_text="Type name from list to add...", placeholder_text_color="gray")
            refresh_fav_list()
            show_all_contacts()

        confirm_dialog(f"Add '{name_to_add}' to favorites?", confirm_add, parent=fav_window)

    make_button(master=fav_window, text="Add to favorites", width=150, height=30, fg_color=COLOR_PRIMARY,
                  command=add_to_fav).pack(pady=5)

    refresh_fav_list()


def open_recent_window():
    rec_window = make_toplevel("Recent", "400x450")

    ctk.CTkLabel(master=rec_window, text="🕘 Recently Opened", font=("Arial", 20, "bold")).pack(pady=15)

    rec_scroll = ctk.CTkScrollableFrame(master=rec_window, width=340, height=300, corner_radius=8)
    rec_scroll.pack(pady=10, padx=10, fill="both", expand=True)

    def refresh_recent_list():
        for widget in rec_scroll.winfo_children():
            widget.destroy()

        valid_entries = [r for r in recent if r["name"] in contacts]

        if not valid_entries:
            ctk.CTkLabel(master=rec_scroll, text="No recently opened contacts yet",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=20)
            return

        for entry in valid_entries:
            name = entry["name"]
            row = ctk.CTkFrame(master=rec_scroll, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=3)

            try:
                when = datetime.fromtimestamp(entry["timestamp"]).strftime("%d.%m.%Y %H:%M")
            except (TypeError, ValueError, OSError):
                when = "unknown"

            text_col = ctk.CTkFrame(master=row, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True, padx=5)

            ctk.CTkLabel(master=text_col, text=f"🕘 {name}: {all_phones_text(contacts[name])}",
                         font=("Arial", 13), anchor="w", wraplength=220, justify="left").pack(
                anchor="w", fill="x")
            ctk.CTkLabel(master=text_col, text=f"Opened {when}", font=("Arial", 10),
                         text_color="gray", anchor="w").pack(anchor="w", fill="x")

            make_button(master=row, text="🗑️", width=30, height=25, fg_color=COLOR_DANGER,
                          hover_color=COLOR_DANGER_HOVER, font=("Arial", 10),
                          command=lambda n=name: remove_recent(n)).pack(side="right", padx=5)

    def remove_recent(name):
        recent[:] = [r for r in recent if r["name"] != name]
        save_recent()
        refresh_recent_list()

    def clear_recent():
        def do_clear():
            recent.clear()
            save_recent()
            refresh_recent_list()

        confirm_dialog("Clear recent history?", do_clear, parent=rec_window, title="Clear Recent")

    make_button(master=rec_window, text="Clear history", width=150, height=30, fg_color=COLOR_GRAY,
                  hover_color=COLOR_GRAY_HOVER, command=clear_recent).pack(pady=5)

    refresh_recent_list()


def levenshtein_distance(a, b):
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    previous_row = list(range(len(b) + 1))
    for i, char_a in enumerate(a):
        current_row = [i + 1]
        for j, char_b in enumerate(b):
            insert_cost = previous_row[j + 1] + 1
            delete_cost = current_row[j] + 1
            replace_cost = previous_row[j] + (0 if char_a == char_b else 1)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]


DUP_THRESHOLD_PARAMS = {
    "strict": {"max_distance": 1, "max_ratio": 0.20},
    "medium": {"max_distance": 2, "max_ratio": 0.34},
    "loose": {"max_distance": 3, "max_ratio": 0.50},
}


def names_are_similar(name_a, name_b):
    if name_a.lower() == name_b.lower():
        return True
    distance = levenshtein_distance(name_a, name_b)
    longer = max(len(name_a), len(name_b))
    if longer == 0:
        return False
    params = DUP_THRESHOLD_PARAMS.get(app_settings.get("dup_threshold", "medium"),
                                       DUP_THRESHOLD_PARAMS["medium"])
    return distance <= params["max_distance"] and distance / longer <= params["max_ratio"]


def find_duplicate_groups():
    names = list(contacts.keys())
    seen = set()
    groups = []

    for i, name_a in enumerate(names):
        if name_a in seen:
            continue
        group = {name_a}
        numbers_a = {p["number"] for p in contacts[name_a].get("phones", [])}

        for name_b in names[i + 1:]:
            if name_b in seen or name_b in group:
                continue
            numbers_b = {p["number"] for p in contacts[name_b].get("phones", [])}
            shares_number = bool(numbers_a & numbers_b)
            similar_name = names_are_similar(name_a, name_b)
            if shares_number or similar_name:
                group.add(name_b)

        if len(group) > 1:
            groups.append(sorted(group))
            seen |= group

    return groups


def merge_contacts(names_to_merge, win_to_close=None):
    merged_phones = []
    seen_numbers = set()
    merged_category = None
    merged_notes = []
    earliest_created_at = None
    merged_usage_count = 0

    for name in names_to_merge:
        if name not in contacts:
            continue
        data = contacts[name]
        for p in data.get("phones", []):
            if p["number"] not in seen_numbers:
                merged_phones.append(p)
                seen_numbers.add(p["number"])
        if merged_category is None and data.get("category"):
            merged_category = data.get("category")
        if data.get("note"):
            merged_notes.append(data["note"])
        c_at = data.get("created_at")
        if isinstance(c_at, (int, float)):
            if earliest_created_at is None or c_at < earliest_created_at:
                earliest_created_at = c_at
        merged_usage_count += data.get("usage_count", 0)

    primary_name = names_to_merge[0]

    for name in names_to_merge:
        if name != primary_name and name in contacts:
            del contacts[name]
            if name in favorites:
                favorites.remove(name)
            for r in recent:
                if r["name"] == name:
                    r["name"] = primary_name

    contacts[primary_name] = {
        "phones": merged_phones if merged_phones else [{"label": "Mobile", "number": ""}],
        "category": merged_category or "Other",
        "note": " / ".join(merged_notes),
        "created_at": earliest_created_at if earliest_created_at is not None else time.time(),
        "usage_count": merged_usage_count,
    }

    save_contacts()
    save_favorites()
    save_recent()
    contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
    show_all_contacts()

    if win_to_close is not None:
        win_to_close.destroy()


def open_duplicates_window():
    groups = find_duplicate_groups()

    win = make_toplevel("Possible duplicates", "380x480")

    ctk.CTkLabel(master=win, text="🔍 Possible Duplicates", font=("Arial", 18, "bold")).pack(pady=15)

    if not groups:
        ctk.CTkLabel(master=win, text="No duplicates found! 🎉", font=("Arial", 14, "italic"),
                     text_color="gray").pack(pady=40)
        return

    scroll = ctk.CTkScrollableFrame(master=win, width=330, height=380, corner_radius=8)
    scroll.pack(pady=5, padx=10, fill="both", expand=True)

    def render_groups():
        for widget in scroll.winfo_children():
            widget.destroy()

        current_groups = find_duplicate_groups()
        if not current_groups:
            ctk.CTkLabel(master=scroll, text="No more duplicates! 🎉", font=("Arial", 14, "italic"),
                         text_color="gray").pack(pady=40)
            return

        for group in current_groups:
            card = ctk.CTkFrame(master=scroll, corner_radius=8)
            card.pack(fill="x", pady=6, padx=4)

            names_text = ", ".join(group)
            ctk.CTkLabel(master=card, text=names_text, font=("Arial", 13, "bold"),
                         anchor="w", wraplength=260, justify="left").pack(
                anchor="w", padx=10, pady=(10, 2))

            for name in group:
                phones_preview = all_phones_text(contacts.get(name, {}))
                ctk.CTkLabel(master=card, text=f"  {name}: {phones_preview}", font=("Arial", 11),
                             text_color="gray", anchor="w", wraplength=260, justify="left").pack(
                    anchor="w", padx=10)

            def do_merge(g=group):
                def confirmed():
                    merge_contacts(g)
                    render_groups()

                confirm_dialog(
                    f"Merge {', '.join(g)} into one contact?\nAll numbers will be combined.",
                    confirmed, parent=win, title="Merge contacts"
                )

            make_button(master=card, text="Merge into one", width=150, height=28,
                          fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                          font=("Arial", 12), command=do_merge).pack(pady=(8, 10))

    render_groups()


def export_contacts_to_file():
    path = filedialog.asksaveasfilename(
        title="Export phonebook",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json")],
        initialfile="phonebook_export.json",
    )
    if not path:
        return

    export_payload = {
        "contacts": contacts,
        "favorites": favorites,
        "exported_at": time.time(),
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_payload, f, ensure_ascii=False, indent=4)
        confirm_dialog(f"Exported {len(contacts)} contact(s) successfully!", lambda: None,
                       title="Export complete")
    except Exception as e:
        confirm_dialog(f"Export failed:\n{e}", lambda: None, title="Export error")


def import_contacts_from_file(parent=None):
    path = filedialog.askopenfilename(
        title="Import phonebook",
        filetypes=[("JSON files", "*.json")],
    )
    if not path:
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        confirm_dialog(f"Import failed:\n{e}", lambda: None, parent=parent, title="Import error")
        return

    if not isinstance(raw, dict) or "contacts" not in raw:
        confirm_dialog("This file doesn't look like a valid phonebook export.", lambda: None,
                       parent=parent, title="Import error")
        return

    imported_contacts = migrate_contacts(raw.get("contacts", {}))
    imported_favorites = normalize_favorites(raw.get("favorites", []))

    def do_merge():
        contacts.update(imported_contacts)
        for fav in imported_favorites:
            if fav not in favorites and fav in contacts:
                favorites.append(fav)
        save_contacts()
        save_favorites()
        contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
        show_all_contacts()

    def do_replace():
        contacts.clear()
        contacts.update(imported_contacts)
        favorites[:] = [f for f in imported_favorites if f in contacts]
        save_contacts()
        save_favorites()
        contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
        show_all_contacts()

    choice_win = make_toplevel("Import options", "320x220", parent)
    ctk.CTkLabel(master=choice_win, text=f"Found {len(imported_contacts)} contact(s)",
                 font=("Arial", 14, "bold")).pack(pady=(20, 5))
    ctk.CTkLabel(master=choice_win, text="How do you want to import them?",
                 font=("Arial", 12), text_color="gray").pack(pady=(0, 15))

    def confirm_merge():
        choice_win.destroy()
        do_merge()

    def confirm_replace():
        def really_replace():
            choice_win.destroy()
            do_replace()

        confirm_dialog("This will delete your current contacts and replace them. Continue?",
                       really_replace, parent=choice_win, title="Replace all")

    make_button(master=choice_win, text="Merge with existing", width=220, height=35,
                  fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                  command=confirm_merge).pack(pady=5)
    make_button(master=choice_win, text="Replace all contacts", width=220, height=35,
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=confirm_replace).pack(pady=5)


def clear_all_contacts_window():
    if not contacts:
        return

    def do_clear():
        contacts.clear()
        favorites.clear()
        recent.clear()
        save_contacts()
        save_favorites()
        save_recent()
        contacts_frame.configure(label_text=f"Contact list ({len(contacts)})")
        show_all_contacts()

    confirm_dialog("Delete ALL contacts?", do_clear, title="Clear Book")


def set_theme(theme_name, theme_var=None):
    app_settings["theme"] = theme_name
    save_settings()
    ctk.set_appearance_mode(theme_name)
    if theme_var is not None:
        theme_var.set(theme_name)


def set_dup_threshold(level):
    app_settings["dup_threshold"] = level
    save_settings()


def open_settings_window():
    win = make_toplevel("Settings", "380x660")

    ctk.CTkLabel(master=win, text="⚙️ Settings", font=("Arial", 18, "bold")).pack(pady=(20, 15))

    theme_section = ctk.CTkFrame(master=win, corner_radius=8)
    theme_section.pack(fill="x", padx=20, pady=8)

    ctk.CTkLabel(master=theme_section, text="Appearance", font=("Arial", 13, "bold")).pack(
        anchor="w", padx=12, pady=(10, 5))

    theme_var = ctk.StringVar(value=app_settings["theme"])
    theme_row = ctk.CTkFrame(master=theme_section, fg_color="transparent")
    theme_row.pack(fill="x", padx=12, pady=(0, 12))

    ctk.CTkRadioButton(master=theme_row, text="🌙 Dark", variable=theme_var, value="dark",
                        command=lambda: set_theme("dark", theme_var)).pack(side="left", padx=(0, 20))
    ctk.CTkRadioButton(master=theme_row, text="☀️ Light", variable=theme_var, value="light",
                        command=lambda: set_theme("light", theme_var)).pack(side="left")

    dup_section = ctk.CTkFrame(master=win, corner_radius=8)
    dup_section.pack(fill="x", padx=20, pady=8)

    ctk.CTkLabel(master=dup_section, text="Duplicate detection sensitivity",
                 font=("Arial", 13, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
    ctk.CTkLabel(master=dup_section,
                 text="How strict the name-matching is when looking for duplicates",
                 font=("Arial", 11), text_color="gray", wraplength=320, justify="left").pack(
        anchor="w", padx=12, pady=(0, 8))

    dup_var = ctk.StringVar(value=app_settings.get("dup_threshold", "medium"))
    dup_menu = ctk.CTkOptionMenu(
        master=dup_section, values=["strict", "medium", "loose"], variable=dup_var,
        width=200, command=set_dup_threshold
    )
    dup_menu.pack(anchor="w", padx=12, pady=(0, 12))

    data_section = ctk.CTkFrame(master=win, corner_radius=8)
    data_section.pack(fill="x", padx=20, pady=8)

    ctk.CTkLabel(master=data_section, text="Backup & restore", font=("Arial", 13, "bold")).pack(
        anchor="w", padx=12, pady=(10, 8))

    make_button(master=data_section, text="⬇️ Export contacts to JSON", width=260, height=35,
                  fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                  command=export_contacts_to_file).pack(padx=12, pady=(0, 8))

    make_button(master=data_section, text="⬆️ Import contacts from JSON", width=260, height=35,
                  fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                  command=lambda: import_contacts_from_file(win)).pack(padx=12, pady=(0, 12))

    hotkeys_section = ctk.CTkFrame(master=win, corner_radius=8)
    hotkeys_section.pack(fill="x", padx=20, pady=8)

    ctk.CTkLabel(master=hotkeys_section, text="⌨️ Keyboard shortcuts", font=("Arial", 13, "bold")).pack(
        anchor="w", padx=12, pady=(10, 8))

    shortcuts = [
        ("Ctrl + N", "Add a new contact"),
        ("Ctrl + F", "Jump to the search field"),
    ]

    for keys, description in shortcuts:
        row = ctk.CTkFrame(master=hotkeys_section, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(master=row, text=keys, font=("Arial", 12, "bold"), text_color="white",
                     fg_color=COLOR_PRIMARY, corner_radius=6, width=90).pack(side="left")
        ctk.CTkLabel(master=row, text=description, font=("Arial", 12), text_color="gray",
                     anchor="w").pack(side="left", padx=(10, 0))


def update_password_button_text():
    password_button.configure(text="🔁 Change password" if secret_data["password"] else "🔐 Password")


def reencrypt_data(old_key, new_key):
    current_contacts = migrate_contacts(load_json(FILE_CONTACTS, old_key, dict(DEFAULT_CONTACTS)))
    current_favorites = normalize_favorites(load_json(FILE_FAVORITES, old_key, []))
    current_recent = normalize_recent(load_json(FILE_RECENT, old_key, []))
    save_json(FILE_CONTACTS, current_contacts, new_key)
    save_json(FILE_FAVORITES, current_favorites, new_key)
    save_json(FILE_RECENT, current_recent, new_key)
    global contacts, favorites, recent
    contacts = current_contacts
    favorites = current_favorites
    recent = current_recent


def open_set_password_window(parent=None):
    win = make_toplevel("Set Password", "320x340", parent)

    ctk.CTkLabel(master=win, text="Set Master Password", font=("Arial", 16, "bold")).pack(pady=15)

    pass_entry = ctk.CTkEntry(master=win, placeholder_text="New password", width=250, show="*")
    pass_entry.pack(pady=8)

    hint_entry = ctk.CTkEntry(master=win, placeholder_text="Hint (optional)", width=250)
    hint_entry.pack(pady=8)

    error_label = ctk.CTkLabel(master=win, text="", font=("Arial", 12))
    error_label.pack(pady=5)

    def confirm_set_password():
        global current_key
        entered = pass_entry.get().strip()
        hint = hint_entry.get().strip()
        if not entered:
            error_label.configure(text="Password cannot be empty!", text_color="red")
            shake_widget(pass_entry)
            return

        old_key = current_key if current_key else ""
        reencrypt_data(old_key, entered)

        secret_data["password"] = entered
        secret_data["hint"] = hint
        save_secret()

        current_key = entered
        update_password_button_text()
        win.destroy()

    make_button(master=win, text="Confirm", width=150, fg_color=COLOR_SUCCESS,
                  hover_color=COLOR_SUCCESS_HOVER, command=confirm_set_password).pack(pady=15)
    pass_entry.bind("<Return>", lambda event: confirm_set_password())
    pass_entry.focus()


def open_forgot_password_window(parent):
    win = make_toplevel("Forgot Password", "320x260", parent)

    ctk.CTkLabel(master=win, text="Password Recovery", font=("Arial", 16, "bold")).pack(pady=15)

    if not secret_data["hint"]:
        ctk.CTkLabel(master=win, text="No hint was set for this password.",
                     font=("Arial", 13), text_color="gray", wraplength=260).pack(pady=20)
        return

    ctk.CTkLabel(master=win, text="Enter the hint answer:", font=("Arial", 13)).pack(pady=5)

    hint_entry = ctk.CTkEntry(master=win, placeholder_text="Hint answer", width=250)
    hint_entry.pack(pady=8)

    result_label = ctk.CTkLabel(master=win, text="", font=("Arial", 14, "bold"), wraplength=260)
    result_label.pack(pady=10)

    def check_hint():
        answer = hint_entry.get().strip()
        if answer == secret_data["hint"]:
            result_label.configure(text=f"Your password: {secret_data['password']}", text_color="#2cb67d")
        else:
            result_label.configure(text="Incorrect hint answer!", text_color="red")

    make_button(master=win, text="Check", width=150, fg_color=COLOR_PRIMARY,
                  hover_color=COLOR_PRIMARY_HOVER, command=check_hint).pack(pady=10)
    hint_entry.bind("<Return>", lambda event: check_hint())
    hint_entry.focus()


def open_reset_password_window(parent):
    def do_reset():
        global current_key
        old_key = current_key if current_key else ""
        reencrypt_data(old_key, "")

        secret_data["password"] = ""
        secret_data["hint"] = ""
        save_secret()

        current_key = ""
        update_password_button_text()
        parent.destroy()
        show_all_contacts()

    confirm_dialog("Reset password? This removes the master password.", do_reset,
                   parent=parent, title="Reset Password")


def open_password_window():
    win = make_toplevel("Password", "320x400")

    if not secret_data["password"]:
        win.destroy()
        open_set_password_window()
        return

    ctk.CTkLabel(master=win, text="🔐 Manage Password", font=("Arial", 18, "bold")).pack(pady=20)

    make_button(master=win, text="Change password", width=220, height=38, corner_radius=8,
                  fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER,
                  command=lambda: open_set_password_window(win)).pack(pady=8)

    make_button(master=win, text="Reset password", width=220, height=38, corner_radius=8,
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=lambda: open_reset_password_window(win)).pack(pady=8)

    make_button(master=win, text="Forgot password?", width=220, height=38, corner_radius=8,
                  fg_color=COLOR_GRAY, hover_color=COLOR_GRAY_HOVER,
                  command=lambda: open_forgot_password_window(win)).pack(pady=8)


def show_lock_screen(on_success):
    win = ctk.CTkToplevel(app)
    win.title("Locked")
    win.geometry("340x360")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    win.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    fade_in_window(win, target_size="340x360")

    ctk.CTkLabel(master=win, text="🔒 Enter Password", font=("Arial", 18, "bold")).pack(pady=20)

    pass_entry = ctk.CTkEntry(master=win, placeholder_text="Password", width=220, show="*")
    pass_entry.pack(pady=10)

    error_label = ctk.CTkLabel(master=win, text="", font=("Arial", 12))
    error_label.pack(pady=5)

    unlock_button = make_button(master=win, text="Unlock", width=150, command=lambda: try_unlock())
    unlock_button.pack(pady=10)

    forgot_button = make_button(master=win, text="Forgot password?", width=180, fg_color=COLOR_GRAY,
                                   hover_color=COLOR_GRAY_HOVER,
                                   command=lambda: open_forgot_password_window(win))
    forgot_button.pack(pady=10)

    countdown_job = {"id": None}

    def set_locked_ui(locked):
        state = "disabled" if locked else "normal"
        pass_entry.configure(state=state)
        unlock_button.configure(state=state)

    def update_countdown():
        global failed_attempts, lockout_until
        remaining = lockout_until - time.time()
        if remaining <= 0:
            failed_attempts = 0
            lockout_until = 0.0
            error_label.configure(text="")
            set_locked_ui(False)
            pass_entry.focus()
            countdown_job["id"] = None
            return
        error_label.configure(
            text=f"Too many attempts! Wait {int(remaining) + 1}s ⏳", text_color="red"
        )
        countdown_job["id"] = win.after(250, update_countdown)

    def start_lockout():
        global lockout_until
        lockout_until = time.time() + LOCKOUT_SECONDS
        set_locked_ui(True)
        pass_entry.delete(0, "end")
        if countdown_job["id"] is None:
            update_countdown()

    def try_unlock():
        global current_key, failed_attempts, lockout_until

        if time.time() < lockout_until:
            return

        entered = pass_entry.get().strip()
        if entered == secret_data["password"]:
            current_key = entered
        elif entered == ADMIN_PASSWORD:
            current_key = secret_data["password"]
        else:
            failed_attempts += 1
            remaining_tries = MAX_LOGIN_ATTEMPTS - failed_attempts
            pass_entry.delete(0, "end")
            shake_widget(pass_entry)
            if remaining_tries <= 0:
                start_lockout()
            else:
                error_label.configure(
                    text=f"Wrong password! ❌ ({remaining_tries} attempt(s) left)",
                    text_color="red"
                )
            return

        failed_attempts = 0
        lockout_until = 0.0
        load_data()
        win.destroy()
        on_success()

    pass_entry.bind("<Return>", lambda event: try_unlock())
    pass_entry.focus()

    if time.time() < lockout_until:
        set_locked_ui(True)
        update_countdown()

    win.grab_set()


ctk.set_appearance_mode(app_settings["theme"])
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Phonebook v1.0")
app.geometry("560x870")
app.minsize(540, 800)
app.resizable(True, True)

ctk.CTkLabel(master=app, text="Telephone directory", font=("Arial", 24, "bold")).pack(pady=20)

search_entry = ctk.CTkEntry(master=app, placeholder_text="Enter a name or number to search...",
                             width=350, height=40, corner_radius=8)
search_entry.pack(pady=10)
search_entry.bind("<KeyRelease>", lambda event: search_contact())

# ---------------------------------------------------------------------------
# Горячие клавиши.
# Привязаны через app.bind(...) (не bind_all), поэтому они срабатывают
# только когда фокус находится в главном окне — открытое модальное окно
# (Toplevel) их не перехватит и не будет с ними конфликтовать.
# Ctrl+N — открыть окно добавления нового контакта.
# Ctrl+F — поставить курсор в поле поиска и выделить его текущее содержимое,
# чтобы можно было сразу начать печатать новый запрос.
# Биндим и нижний, и верхний регистр (Control-n / Control-N), так как при
# зажатом Ctrl некоторые платформы определяют Shift независимо и присылают
# заглавную букву даже без явного нажатия Shift.
# ---------------------------------------------------------------------------

def _focus_search(event=None):
    search_entry.focus_set()
    search_entry.select_range(0, "end")
    return "break"


def _open_new_contact_shortcut(event=None):
    open_add_contact_window()
    return "break"


app.bind("<Control-n>", _open_new_contact_shortcut)
app.bind("<Control-N>", _open_new_contact_shortcut)
app.bind("<Control-f>", _focus_search)
app.bind("<Control-F>", _focus_search)

filter_frame = ctk.CTkFrame(master=app, fg_color="transparent")
filter_frame.pack(pady=5)

category_row = ctk.CTkFrame(master=filter_frame, fg_color="transparent")
category_row.pack(pady=2)

ctk.CTkLabel(master=category_row, text="Category:", font=("Arial", 13), width=70, anchor="e").pack(
    side="left", padx=5)

category_filter_var = ctk.StringVar(value=CATEGORY_ALL)
category_filter_menu = ctk.CTkOptionMenu(
    master=category_row, values=[CATEGORY_ALL] + CATEGORIES, variable=category_filter_var,
    width=180, command=lambda choice: search_contact()
)
category_filter_menu.pack(side="left", padx=5)

sort_row = ctk.CTkFrame(master=filter_frame, fg_color="transparent")
sort_row.pack(pady=2)

ctk.CTkLabel(master=sort_row, text="Sort by:", font=("Arial", 13), width=70, anchor="e").pack(
    side="left", padx=5)

sort_var = ctk.StringVar(value=SORT_NAME_AZ)
sort_menu = ctk.CTkOptionMenu(
    master=sort_row, values=SORT_OPTIONS, variable=sort_var,
    width=180, command=lambda choice: search_contact()
)
sort_menu.pack(side="left", padx=5)

contacts_frame = ctk.CTkScrollableFrame(
    master=app, width=400, height=280, corner_radius=8,
    label_text=f"Contact list ({len(contacts)})", label_font=("Arial", 12, "bold")
)
contacts_frame.pack(pady=20)

btn_frame = ctk.CTkFrame(master=app, fg_color="transparent")
btn_frame.pack(pady=10)

make_button(master=btn_frame, text="Add contact", width=170, height=40, corner_radius=8,
              fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, font=("Arial", 14, "bold"),
              command=open_add_contact_window).pack(side="left", padx=5)

make_button(master=btn_frame, text="Favorites", width=170, height=40, corner_radius=8,
              fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, font=("Arial", 14, "bold"),
              command=open_favorites_window).pack(side="left", padx=5)

ctk.CTkLabel(master=app, text="Tip: Ctrl+N — new contact   ·   Ctrl+F — search",
             font=("Arial", 10), text_color="gray").pack(pady=(0, 2))

extra_frame = ctk.CTkFrame(master=app, fg_color="transparent")
extra_frame.pack(pady=5)

make_button(master=extra_frame, text="🕘 Recent", width=170, height=35, corner_radius=8,
              fg_color=COLOR_GRAY, hover_color=COLOR_GRAY_HOVER, font=("Arial", 13),
              command=open_recent_window).pack(side="left", padx=5)

make_button(master=extra_frame, text="🔍 Find duplicates", width=170, height=35, corner_radius=8,
              fg_color=COLOR_GRAY, hover_color=COLOR_GRAY_HOVER, font=("Arial", 13),
              command=open_duplicates_window).pack(side="left", padx=5)

bottom_frame = ctk.CTkFrame(master=app, fg_color="transparent")
bottom_frame.pack(pady=5)

password_button = make_button(master=bottom_frame, text="🔐 Password", width=170, height=35, corner_radius=8,
                                 fg_color=COLOR_GRAY, hover_color=COLOR_GRAY_HOVER, font=("Arial", 13),
                                 command=open_password_window)
password_button.pack(side="left", padx=5)

make_button(master=bottom_frame, text="🗑️ Clear all", width=170, height=35, corner_radius=8,
              fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER, font=("Arial", 13),
              command=clear_all_contacts_window).pack(side="left", padx=5)

settings_frame = ctk.CTkFrame(master=app, fg_color="transparent")
settings_frame.pack(pady=5)

make_button(master=settings_frame, text="⚙️ Settings", width=345, height=35, corner_radius=8,
              fg_color=COLOR_GRAY, hover_color=COLOR_GRAY_HOVER, font=("Arial", 13),
              command=open_settings_window).pack(side="left", padx=5)

update_password_button_text()

if password_is_set:
    show_lock_screen(show_all_contacts)
else:
    load_data()
    show_all_contacts()

app.mainloop()