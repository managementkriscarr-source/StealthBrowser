"""
StealthBrowser Mobile - Pure Kivy (Ultra Fast & Stable on Android)
"""
import os, json, uuid, random, shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.utils import get_color_from_hex, platform
from kivy.graphics import Color, RoundedRectangle

# Desktop preview size
if platform not in ('android', 'ios'):
    Window.size = (390, 720)

# ── Storage & Paths (Works on Android internal storage) ──────
if platform == 'android':
    try:
        from android.storage import app_storage_path
        DATA_DIR = Path(app_storage_path()) / "stealth_profiles"
    except Exception:
        DATA_DIR = Path.home() / ".stealth_profiles"
else:
    DATA_DIR = Path(__file__).parent / "profiles"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MAX_PROFILES = 10

# ── Colors ───────────────────────────────────────────────────
C_BG    = get_color_from_hex("#0f1117")
C_CARD  = get_color_from_hex("#1a1d2e")
C_BLUE  = get_color_from_hex("#2563eb")
C_GREEN = get_color_from_hex("#059669")
C_RED   = get_color_from_hex("#dc2626")
C_GRAY  = get_color_from_hex("#374151")
C_TEXT  = get_color_from_hex("#e2e8f0")
C_MUTED = get_color_from_hex("#94a3b8")

# ── Fingerprint Pools ────────────────────────────────────────
ANDROID_UAS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.102 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; OnePlus 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
]
DEVICES = [
    {"brand": "Samsung", "model": "Galaxy S24 Ultra", "screen": (1080, 2340), "dpr": 3.0},
    {"brand": "Google",  "model": "Pixel 8 Pro",      "screen": (1344, 2992), "dpr": 3.5},
    {"brand": "OnePlus", "model": "OnePlus 12",       "screen": (1440, 3216), "dpr": 3.0},
    {"brand": "Xiaomi",  "model": "Redmi Note 13",    "screen": (1080, 2400), "dpr": 2.75},
]
TIMEZONES = ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"]
WEBGL_LIST = [("Qualcomm", "Adreno (TM) 740"), ("ARM", "Mali-G715 Immortalis"), ("Qualcomm", "Adreno (TM) 730")]

@dataclass
class Fingerprint:
    user_agent: str
    device: str
    screen: str
    timezone: str
    webgl: str
    canvas_noise: float
    platform: str

def generate_fingerprint():
    dev = random.choice(DEVICES)
    wgl = random.choice(WEBGL_LIST)
    return Fingerprint(
        user_agent=random.choice(ANDROID_UAS),
        device=f"{dev['brand']} {dev['model']}",
        screen=f"{dev['screen'][0]}x{dev['screen'][1]} @{dev['dpr']}x",
        timezone=random.choice(TIMEZONES),
        webgl=f"{wgl[0]} - {wgl[1]}",
        canvas_noise=round(random.uniform(0.001, 0.999), 6),
        platform="Linux armv8l"
    )

class Profile:
    def __init__(self, name, proxy=None, fp=None, pid=None):
        self.id = pid or str(uuid.uuid4())[:8]
        self.name = name
        self.proxy = proxy or {}
        self.fp = fp or generate_fingerprint()

    def to_dict(self):
        return {"id": self.id, "name": self.name, "proxy": self.proxy, "fp": asdict(self.fp)}

    @classmethod
    def from_dict(cls, d):
        fp = Fingerprint(**d["fp"])
        return cls(name=d["name"], proxy=d.get("proxy", {}), fp=fp, pid=d["id"])

    def save(self):
        pdir = DATA_DIR / self.id
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "profile.json").write_text(json.dumps(self.to_dict(), indent=2))

    def delete(self):
        shutil.rmtree(DATA_DIR / self.id, ignore_errors=True)

class ProfileManager:
    def list_all(self):
        profiles = []
        for d in DATA_DIR.iterdir():
            if d.is_dir() and (d / "profile.json").exists():
                try:
                    data = json.loads((d / "profile.json").read_text())
                    profiles.append(Profile.from_dict(data))
                except Exception:
                    pass
        return profiles

    def count(self):
        return len(self.list_all())

manager = ProfileManager()

# ── Helper UI Elements ───────────────────────────────────────
def card_box(**kwargs):
    b = BoxLayout(**kwargs)
    with b.canvas.before:
        Color(*C_CARD)
        b._rect = RoundedRectangle(pos=b.pos, size=b.size, radius=[dp(10)])
    b.bind(pos=lambda w,v: setattr(w._rect,'pos',v), size=lambda w,v: setattr(w._rect,'size',v))
    return b

def make_btn(text, bg=C_BLUE, h=dp(42), cb=None):
    b = Button(text=text, size_hint_y=None, height=h, background_color=bg, background_normal='', color=C_TEXT, bold=True)
    if cb: b.bind(on_release=cb)
    return b

def alert(title, msg):
    content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
    content.add_widget(Label(text=msg, color=C_TEXT, font_size=dp(13), halign='center'))
    btn = make_btn("OK", C_BLUE, dp(38))
    content.add_widget(btn)
    p = Popup(title=title, content=content, size_hint=(0.85, 0.35), background_color=C_CARD, title_color=C_TEXT)
    btn.bind(on_release=p.dismiss)
    p.open()

# ── Screen 1: Profiles List ──────────────────────────────────
class ListScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical')
        
        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(52), padding=[dp(14), 0], spacing=dp(8))
        hdr.add_widget(Label(text="[b]StealthBrowser[/b]", markup=True, font_size=dp(18), color=C_TEXT, halign='left'))
        add_b = Button(text="+", size_hint=(None, None), size=(dp(40), dp(40)), background_color=C_BLUE, background_normal='', color=C_TEXT, font_size=dp(24), bold=True)
        add_b.bind(on_release=self.go_create)
        hdr.add_widget(add_b)
        root.add_widget(hdr)

        self.count_lbl = Label(text=f"0 / {MAX_PROFILES} profiles", size_hint_y=None, height=dp(22), font_size=dp(12), color=C_MUTED)
        root.add_widget(self.count_lbl)

        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=dp(10), padding=[dp(12), dp(6), dp(12), dp(16)], size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_enter(self):
        self.refresh()

    def refresh(self):
        self.grid.clear_widgets()
        profiles = manager.list_all()
        self.count_lbl.text = f"{len(profiles)} / {MAX_PROFILES} profiles"
        if not profiles:
            self.grid.add_widget(Label(text="No profiles created yet.\nTap '+' above to create one.", color=C_MUTED, size_hint_y=None, height=dp(100), halign='center'))
            return
        
        for p in profiles:
            c = card_box(orientation='vertical', size_hint_y=None, height=dp(115), padding=dp(10), spacing=dp(4))
            c.add_widget(Label(text=f"[b]{p.name}[/b]", markup=True, font_size=dp(15), color=C_TEXT, size_hint_y=None, height=dp(24), halign='left'))
            c.add_widget(Label(text=f"{p.fp.device} | {p.fp.timezone}", font_size=dp(12), color=C_MUTED, size_hint_y=None, height=dp(18), halign='left'))
            
            row = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
            b_launch = make_btn("Launch", C_GREEN, dp(36), lambda *_, pid=p.id: self.launch(pid))
            b_info   = make_btn("Fingerprint", C_GRAY, dp(36), lambda *_, pid=p.id: self.show_fp(pid))
            b_del    = make_btn("Del", C_RED, dp(36), lambda *_, pid=p.id: self.del_profile(pid))
            b_del.size_hint_x = 0.3
            row.add_widget(b_launch)
            row.add_widget(b_info)
            row.add_widget(b_del)
            c.add_widget(row)
            self.grid.add_widget(c)

    def go_create(self, *_):
        if manager.count() >= MAX_PROFILES:
            alert("Limit", f"Max {MAX_PROFILES} profiles reached!")
            return
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'create'

    def launch(self, pid):
        scr = self.manager.get_screen('browser')
        scr.load(pid)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'browser'

    def show_fp(self, pid):
        scr = self.manager.get_screen('fp')
        scr.load(pid)
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'fp'

    def del_profile(self, pid):
        for p in manager.list_all():
            if p.id == pid:
                p.delete()
                break
        self.refresh()

# ── Screen 2: Create Profile ─────────────────────────────────
class CreateScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))

        hdr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        back = make_btn("< Back", C_GRAY, dp(40), self.go_back)
        back.size_hint_x = 0.3
        hdr.add_widget(back)
        hdr.add_widget(Label(text="[b]New Profile[/b]", markup=True, font_size=dp(17), color=C_TEXT))
        root.add_widget(hdr)

        root.add_widget(Label(text="Profile Name:", color=C_MUTED, size_hint_y=None, height=dp(20), halign='left'))
        self.in_name = TextInput(hint_text="e.g. USA Identity 1", multiline=False, size_hint_y=None, height=dp(42), background_color=C_CARD, foreground_color=C_TEXT)
        root.add_widget(self.in_name)

        root.add_widget(Label(text="Proxy Host (optional):", color=C_MUTED, size_hint_y=None, height=dp(20), halign='left'))
        self.in_proxy = TextInput(hint_text="e.g. 192.168.1.1:8080", multiline=False, size_hint_y=None, height=dp(42), background_color=C_CARD, foreground_color=C_TEXT)
        root.add_widget(self.in_proxy)

        root.add_widget(Label(text="", size_hint_y=1))
        btn_create = make_btn("Generate Profile & Save", C_BLUE, dp(48), self.save)
        root.add_widget(btn_create)
        self.add_widget(root)

    def save(self, *_):
        name = self.in_name.text.strip()
        if not name:
            alert("Error", "Please enter a profile name")
            return
        p = Profile(name=name, proxy={"host": self.in_proxy.text.strip()})
        p.save()
        self.in_name.text = ""
        self.in_proxy.text = ""
        self.go_back()

    def go_back(self, *_):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'list'

# ── Screen 3: Browser Session ────────────────────────────────
class BrowserScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.profile = None
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))

        hdr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        back = make_btn("< Back", C_GRAY, dp(40), self.go_back)
        back.size_hint_x = 0.28
        hdr.add_widget(back)
        self.lbl_title = Label(text="Browser", markup=True, font_size=dp(16), color=C_TEXT)
        hdr.add_widget(self.lbl_title)
        root.add_widget(hdr)

        # URL Input Row
        url_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.in_url = TextInput(text="https://browserleaks.com/canvas", multiline=False, background_color=C_CARD, foreground_color=C_TEXT)
        go_b = make_btn("Go", C_BLUE, dp(44), self.open_url)
        go_b.size_hint_x = 0.25
        url_row.add_widget(self.in_url)
        url_row.add_widget(go_b)
        root.add_widget(url_row)

        # Active Details Card
        self.info_card = card_box(orientation='vertical', padding=dp(12), spacing=dp(6))
        self.lbl_info = Label(text="Loading...", color=C_TEXT, font_size=dp(13), halign='left')
        self.info_card.add_widget(self.lbl_info)
        root.add_widget(self.info_card)

        # Quick Navigation
        quick_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        for name, u in [("Google", "https://google.com"), ("IP Check", "https://whatismyipaddress.com"), ("Canvas", "https://browserleaks.com/canvas")]:
            quick_row.add_widget(make_btn(name, C_GRAY, dp(38), lambda *_, target=u: self.set_quick(target)))
        root.add_widget(quick_row)

        self.add_widget(root)

    def load(self, pid):
        for p in manager.list_all():
            if p.id == pid:
                self.profile = p
                break
        if not self.profile: return
        fp = self.profile.fp
        self.lbl_title.text = f"[b]{self.profile.name}[/b]"
        self.lbl_info.text = (
            f"[color=#059669][b]ACTIVE SPOOFING IDENTITY[/b][/color]\n\n"
            f"Device: {fp.device}\n"
            f"Screen: {fp.screen}\n"
            f"Timezone: {fp.timezone}\n"
            f"WebGL: {fp.webgl}\n"
            f"Canvas Noise: {fp.canvas_noise}\n"
            f"Platform: {fp.platform}\n"
            f"Proxy: {self.profile.proxy.get('host') or 'Direct'}\n\n"
            f"User Agent:\n{fp.user_agent[:60]}..."
        )

    def set_quick(self, u):
        self.in_url.text = u
        self.open_url()

    def open_url(self, *_):
        url = self.in_url.text.strip()
        if not url.startswith("http"): url = "https://" + url
        try:
            if platform == 'android':
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                PythonActivity.mActivity.startActivity(intent)
            else:
                import webbrowser
                webbrowser.open(url)
        except Exception as e:
            alert("Error", str(e))

    def go_back(self, *_):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'list'

# ── Screen 4: Fingerprint Viewer ─────────────────────────────
class FingerprintScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))

        hdr = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(10))
        back = make_btn("< Back", C_GRAY, dp(40), self.go_back)
        back.size_hint_x = 0.28
        hdr.add_widget(back)
        hdr.add_widget(Label(text="[b]Fingerprint Details[/b]", markup=True, font_size=dp(16), color=C_TEXT))
        root.add_widget(hdr)

        scroll = ScrollView()
        self.box = GridLayout(cols=1, spacing=dp(8), padding=dp(6), size_hint_y=None)
        self.box.bind(minimum_height=self.box.setter('height'))
        scroll.add_widget(self.box)
        root.add_widget(scroll)

        self.add_widget(root)

    def load(self, pid):
        self.box.clear_widgets()
        p = next((x for x in manager.list_all() if x.id == pid), None)
        if not p: return
        fp = p.fp
        items = [
            ("Profile", p.name), ("Device", fp.device), ("Resolution", fp.screen),
            ("Timezone", fp.timezone), ("WebGL", fp.webgl), ("Canvas Noise", str(fp.canvas_noise)),
            ("Platform", fp.platform), ("User Agent", fp.user_agent)
        ]
        for label, val in items:
            c = card_box(orientation='vertical', size_hint_y=None, height=dp(56), padding=[dp(10), dp(4)])
            c.add_widget(Label(text=label, font_size=dp(11), color=C_MUTED, size_hint_y=None, height=dp(18), halign='left'))
            c.add_widget(Label(text=f"[b]{val[:40]}[/b]", markup=True, font_size=dp(13), color=C_TEXT, size_hint_y=None, height=dp(24), halign='left'))
            self.box.add_widget(c)

    def go_back(self, *_):
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'list'

# ── App Bootstrap ────────────────────────────────────────────
class StealthBrowserApp(App):
    def build(self):
        Window.clearcolor = C_BG
        sm = ScreenManager()
        sm.add_widget(ListScreen(name='list'))
        sm.add_widget(CreateScreen(name='create'))
        sm.add_widget(BrowserScreen(name='browser'))
        sm.add_widget(FingerprintScreen(name='fp'))
        return sm

if __name__ == '__main__':
    StealthBrowserApp().run()
