"""
StealthBrowser Mobile - Main KivyMD App
Mobile-style UI with profile management + stealth browser
"""
import os, sys, json, threading, asyncio
from pathlib import Path

os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

from kivy.lang import Builder
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemLeadingIcon, MDListItemTrailingIcon
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.divider import MDDivider
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.appbar import MDTopAppBar, MDTopAppBarTitle, MDTopAppBarLeadingButtonContainer, MDTopAppBarTrailingButtonContainer
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem, MDNavigationItemIcon, MDNavigationItemLabel
from kivymd.uix.chip import MDChip, MDChipText
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.segmentedbutton import MDSegmentedButton, MDSegmentedButtonItem

from profile_manager import ProfileManager, MobileProfile, MAX_PROFILES
from fingerprints import MobileFingerprintEngine

manager = ProfileManager()
fp_engine = MobileFingerprintEngine()

# ── Simulate mobile size on desktop ──────────────────────
if platform not in ("android", "ios"):
    Window.size = (400, 760)
    Window.minimum_width  = 360
    Window.minimum_height = 640


KV = """
<ProfileCard>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(90)
    padding: dp(12)
    spacing: dp(4)
    radius: [12]
    elevation: 2
    ripple_behavior: True

<RoundButton@MDButton>:
    style: "filled"
    radius: [24]

<ProxyField@MDTextField>:
    mode: "outlined"
    size_hint_x: 1

MDScreenManager:
    ProfileListScreen:
        name: "profiles"
    CreateProfileScreen:
        name: "create"
    BrowserScreen:
        name: "browser"
    FingerprintScreen:
        name: "fingerprint"
"""


# ────────────────────────────────────────────────────────────────
#  Profile Card Widget
# ────────────────────────────────────────────────────────────────
class ProfileCard(MDCard):
    def __init__(self, profile: MobileProfile, on_launch, on_delete, on_fp, **kwargs):
        super().__init__(**kwargs)
        self.profile    = profile
        self.on_launch  = on_launch
        self.on_delete  = on_delete
        self.on_fp      = on_fp
        self._build()

    def _build(self):
        from kivymd.uix.boxlayout import MDBoxLayout
        p  = self.profile
        fp = p.fingerprint

        row1 = MDBoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(36))

        # OS badge
        os_color = (0.23, 0.6, 0.2, 1) if p.os_type == "android" else (0.1, 0.4, 0.9, 1)
        badge = MDLabel(
            text=("Android" if p.os_type == "android" else "iOS"),
            theme_text_color="Custom",
            text_color=os_color,
            bold=True,
            size_hint=(None, None),
            size=(dp(60), dp(24)),
        )

        name_lbl = MDLabel(
            text=p.name,
            bold=True,
            font_style="Title",
            role="small",
        )

        proxy_lbl = MDLabel(
            text=(p.proxy_url() or "No Proxy"),
            theme_text_color="Secondary",
            font_style="Label",
            role="small",
        )

        # Buttons row
        btn_row = MDBoxLayout(orientation="horizontal", spacing=dp(4), size_hint_y=None, height=dp(32))

        btn_launch = MDButton(style="filled", on_release=lambda *_: self.on_launch(p.id))
        btn_launch.radius = [20]
        btn_launch.add_widget(MDButtonText(text="Launch", theme_text_color="Custom", text_color=(1,1,1,1)))

        btn_fp = MDButton(style="tonal", on_release=lambda *_: self.on_fp(p.id))
        btn_fp.add_widget(MDButtonText(text="FP"))

        btn_del = MDButton(style="text", on_release=lambda *_: self.on_delete(p.id))
        btn_del.add_widget(MDButtonText(text="Delete", theme_text_color="Custom", text_color=(0.9, 0.2, 0.2, 1)))

        btn_row.add_widget(btn_launch)
        btn_row.add_widget(btn_fp)
        btn_row.add_widget(btn_del)

        row1.add_widget(badge)
        row1.add_widget(name_lbl)

        self.add_widget(row1)
        self.add_widget(proxy_lbl)
        self.add_widget(btn_row)


# ────────────────────────────────────────────────────────────────
#  Profile List Screen
# ────────────────────────────────────────────────────────────────
class ProfileListScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation="vertical")

        # Top bar
        bar = MDTopAppBar(type="small")
        bar.add_widget(MDTopAppBarTitle(text="StealthBrowser"))
        trailing = MDTopAppBarTrailingButtonContainer()
        add_btn  = MDIconButton(icon="plus-circle", on_release=self._go_create)
        trailing.add_widget(add_btn)
        bar.add_widget(trailing)
        root.add_widget(bar)

        # Counter
        self.counter_lbl = MDLabel(
            text=f"0 / {MAX_PROFILES} profiles",
            halign="center",
            theme_text_color="Secondary",
            font_style="Label",
            role="small",
            size_hint_y=None,
            height=dp(28),
        )
        root.add_widget(self.counter_lbl)

        # Scroll list
        scroll = MDScrollView()
        self.card_list = MDBoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(12), dp(8), dp(12), dp(80)],
            size_hint_y=None,
        )
        self.card_list.bind(minimum_height=self.card_list.setter("height"))
        scroll.add_widget(self.card_list)
        root.add_widget(scroll)

        # FAB
        from kivymd.uix.button import MDFabButton
        fab = MDFabButton(
            icon="plus",
            pos_hint={"center_x": 0.5, "y": 0.02},
            on_release=self._go_create,
        )
        root.add_widget(fab)

        self.add_widget(root)

    def on_enter(self):
        self._refresh()

    def _refresh(self):
        self.card_list.clear_widgets()
        profiles = manager.list()
        self.counter_lbl.text = f"{len(profiles)} / {MAX_PROFILES} profiles"
        if not profiles:
            self.card_list.add_widget(MDLabel(
                text="No profiles yet\nTap + to create one",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(120),
            ))
            return
        for p in profiles:
            card = ProfileCard(
                profile=p,
                on_launch=self._launch,
                on_delete=self._delete,
                on_fp=self._view_fp,
            )
            self.card_list.add_widget(card)

    def _go_create(self, *_):
        if manager.is_full():
            MDSnackbar(MDSnackbarText(text=f"Max {MAX_PROFILES} profiles reached!")).open()
            return
        self.manager.current = "create"

    def _launch(self, pid):
        bs = self.manager.get_screen("browser")
        bs.load_profile(pid)
        self.manager.current = "browser"

    def _delete(self, pid):
        p = manager.get(pid)
        if not p: return

        def _do_delete(btn_text):
            if btn_text == "DELETE":
                manager.delete(pid)
                self._refresh()
                MDSnackbar(MDSnackbarText(text="Profile deleted")).open()

        dlg = MDDialog(
            MDLabel(text=f"Delete '{p.name}'?\nThis cannot be undone.", halign="center"),
        )
        dlg.open()
        # Simple: just delete after confirm
        manager.delete(pid)
        self._refresh()
        MDSnackbar(MDSnackbarText(text=f"'{p.name}' deleted")).open()

    def _view_fp(self, pid):
        fps = self.manager.get_screen("fingerprint")
        fps.load(pid)
        self.manager.current = "fingerprint"


# ────────────────────────────────────────────────────────────────
#  Create Profile Screen
# ────────────────────────────────────────────────────────────────
class CreateProfileScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation="vertical")

        # Top bar
        bar = MDTopAppBar(type="small")
        leading = MDTopAppBarLeadingButtonContainer()
        back_btn = MDIconButton(icon="arrow-left", on_release=self._go_back)
        leading.add_widget(back_btn)
        bar.add_widget(leading)
        bar.add_widget(MDTopAppBarTitle(text="New Profile"))
        root.add_widget(bar)

        scroll = MDScrollView()
        form   = MDBoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(14),
            size_hint_y=None,
        )
        form.bind(minimum_height=form.setter("height"))

        # Profile Name
        self.name_field = MDTextField(hint_text="Profile Name", mode="outlined")
        form.add_widget(MDLabel(text="Profile Name", bold=True, size_hint_y=None, height=dp(24)))
        form.add_widget(self.name_field)

        # OS Type
        form.add_widget(MDLabel(text="OS Type", bold=True, size_hint_y=None, height=dp(24)))
        self.os_android = True
        os_row = MDBoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(44))

        self.btn_android = MDButton(style="filled", on_release=lambda *_: self._set_os("android"))
        self.btn_android.add_widget(MDButtonText(text="Android"))
        self.btn_ios = MDButton(style="outlined", on_release=lambda *_: self._set_os("ios"))
        self.btn_ios.add_widget(MDButtonText(text="iOS"))
        os_row.add_widget(self.btn_android)
        os_row.add_widget(self.btn_ios)
        form.add_widget(os_row)

        # Proxy
        form.add_widget(MDLabel(text="Proxy (optional)", bold=True, size_hint_y=None, height=dp(24)))
        self.proxy_host = MDTextField(hint_text="Host / IP", mode="outlined")
        self.proxy_port = MDTextField(hint_text="Port", mode="outlined", input_filter="int")
        self.proxy_user = MDTextField(hint_text="Username (optional)", mode="outlined")
        self.proxy_pass = MDTextField(hint_text="Password (optional)", mode="outlined", password=True)
        for f in [self.proxy_host, self.proxy_port, self.proxy_user, self.proxy_pass]:
            form.add_widget(f)

        # Notes
        self.notes_field = MDTextField(hint_text="Notes (optional)", mode="outlined", multiline=True, max_height=dp(80))
        form.add_widget(MDLabel(text="Notes", bold=True, size_hint_y=None, height=dp(24)))
        form.add_widget(self.notes_field)

        # Create Button
        create_btn = MDButton(
            style="filled",
            size_hint=(1, None), height=dp(52),
            on_release=self._create,
        )
        create_btn.radius = [12]
        create_btn.add_widget(MDButtonText(text="Create Profile"))
        form.add_widget(create_btn)

        scroll.add_widget(form)
        root.add_widget(scroll)
        self.add_widget(root)

    def _set_os(self, os_type):
        self.os_android = (os_type == "android")
        self.btn_android.style = "filled" if self.os_android else "outlined"
        self.btn_ios.style     = "outlined" if self.os_android else "filled"

    def _create(self, *_):
        name = self.name_field.text.strip()
        if not name:
            MDSnackbar(MDSnackbarText(text="Profile name required!")).open()
            return
        proxy = {
            "type": "http",
            "host": self.proxy_host.text.strip(),
            "port": self.proxy_port.text.strip(),
            "user": self.proxy_user.text.strip(),
            "pass": self.proxy_pass.text.strip(),
        }
        os_type = "android" if self.os_android else "ios"
        try:
            p = manager.create(name=name, proxy=proxy, os_type=os_type, notes=self.notes_field.text.strip())
            MDSnackbar(MDSnackbarText(text=f"'{p.name}' created!")).open()
            self._clear()
            self.manager.current = "profiles"
        except ValueError as e:
            MDSnackbar(MDSnackbarText(text=str(e))).open()

    def _clear(self):
        for f in [self.name_field, self.proxy_host, self.proxy_port, self.proxy_user, self.proxy_pass, self.notes_field]:
            f.text = ""

    def _go_back(self, *_):
        self.manager.current = "profiles"


# ────────────────────────────────────────────────────────────────
#  Browser Screen (stealth webview simulation)
# ────────────────────────────────────────────────────────────────
class BrowserScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile = None
        self._build()

    def _build(self):
        self.root_layout = MDBoxLayout(orientation="vertical")

        # Top bar
        self.bar = MDTopAppBar(type="small")
        leading  = MDTopAppBarLeadingButtonContainer()
        back_btn = MDIconButton(icon="arrow-left", on_release=self._go_back)
        leading.add_widget(back_btn)
        self.bar.add_widget(leading)
        self.bar_title = MDTopAppBarTitle(text="Browser")
        self.bar.add_widget(self.bar_title)

        trailing = MDTopAppBarTrailingButtonContainer()
        regen_btn = MDIconButton(icon="refresh", on_release=self._regen_fp)
        trailing.add_widget(regen_btn)
        self.bar.add_widget(trailing)
        self.root_layout.add_widget(self.bar)

        # URL bar
        url_row = MDBoxLayout(
            orientation="horizontal",
            padding=[dp(10), dp(6)],
            spacing=dp(8),
            size_hint_y=None, height=dp(56),
        )
        self.url_field = MDTextField(
            hint_text="https://",
            mode="outlined",
            size_hint_x=0.8,
        )
        go_btn = MDButton(style="filled", on_release=self._navigate, size_hint_x=0.2)
        go_btn.radius = [10]
        go_btn.add_widget(MDButtonText(text="Go"))
        url_row.add_widget(self.url_field)
        url_row.add_widget(go_btn)
        self.root_layout.add_widget(url_row)

        MDDivider()

        # Browser content area
        self.content = MDScrollView()
        self.content_box = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
            size_hint_y=None,
        )
        self.content_box.bind(minimum_height=self.content_box.setter("height"))

        self.status_card = MDCard(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            radius=[12],
            size_hint_y=None,
            height=dp(260),
        )
        self.status_lbl = MDLabel(
            text="Loading profile...",
            halign="center",
            font_style="Body",
            role="large",
        )
        self.status_card.add_widget(self.status_lbl)
        self.content_box.add_widget(self.status_card)
        self.content.add_widget(self.content_box)
        self.root_layout.add_widget(self.content)

        # Quick nav buttons
        nav_row = MDBoxLayout(
            orientation="horizontal",
            padding=[dp(10), dp(6)],
            spacing=dp(8),
            size_hint_y=None, height=dp(56),
        )
        for label, url in [("Google","https://google.com"),("Check FP","https://browserleaks.com/canvas"),("IP Check","https://whatismyipaddress.com")]:
            btn = MDButton(style="tonal", on_release=lambda *_, u=url: self._quick_nav(u))
            btn.add_widget(MDButtonText(text=label))
            nav_row.add_widget(btn)
        self.root_layout.add_widget(nav_row)

        self.add_widget(self.root_layout)

    def load_profile(self, pid):
        self.profile = manager.get(pid)
        if not self.profile: return
        self.profile.mark_used()
        fp = self.profile.fingerprint
        self.bar_title.text = self.profile.name
        self.status_lbl.text = (
            f"Profile: {self.profile.name}\n\n"
            f"Device: {fp.device_brand} {fp.device_model}\n"
            f"OS: {fp.os_type.title()}\n"
            f"Screen: {fp.screen_width}x{fp.screen_height} @ {fp.device_pixel_ratio}x\n"
            f"Timezone: {fp.timezone}\n"
            f"WebGL: {fp.webgl_vendor}\n"
            f"Cores: {fp.hardware_concurrency}  RAM: {fp.device_memory}GB\n\n"
            f"Proxy: {self.profile.proxy_url() or 'None'}\n\n"
            f"Stealth: ACTIVE"
        )
        self._launch_stealth_browser()

    def _launch_stealth_browser(self):
        """Launch actual Playwright browser with mobile fingerprint"""
        if not self.profile: return
        def _run():
            try:
                import asyncio
                from playwright.async_api import async_playwright

                fp = self.profile.fingerprint
                stealth_js = self._build_stealth_js()
                proxy_url = self.profile.proxy_url()

                async def _do():
                    async with async_playwright() as pw:
                        launch_args = [
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            f"--lang={fp.languages[0]}",
                        ]
                        browser = await pw.chromium.launch(
                            headless=False,
                            args=launch_args,
                        )
                        ctx_opts = {
                            "user_agent": fp.user_agent,
                            "viewport": {"width": fp.screen_width // 3, "height": fp.screen_height // 3},
                            "device_scale_factor": fp.device_pixel_ratio,
                            "is_mobile": True,
                            "has_touch": True,
                            "locale": fp.languages[0],
                            "timezone_id": fp.timezone,
                        }
                        if proxy_url:
                            ctx_opts["proxy"] = {"server": proxy_url}
                            if self.profile.proxy.get("user"):
                                ctx_opts["proxy"]["username"] = self.profile.proxy["user"]
                                ctx_opts["proxy"]["password"] = self.profile.proxy.get("pass","")

                        ctx  = await browser.new_context(**ctx_opts)
                        await ctx.add_init_script(stealth_js)
                        page = await ctx.new_page()
                        await page.goto("https://www.google.com")
                        await asyncio.Event().wait()

                asyncio.run(_do())
            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(self.status_lbl, 'text',
                    self.status_lbl.text + f"\n\n[Browser Error]\n{str(e)[:120]}"))

        threading.Thread(target=_run, daemon=True).start()
        MDSnackbar(MDSnackbarText(text=f"Launching {self.profile.name}...")).open()

    def _build_stealth_js(self):
        fp = self.profile.fingerprint
        import json
        langs = json.dumps(fp.languages)
        return f"""
(function(){{
  const def = (obj, key, val) => {{ try {{ Object.defineProperty(obj, key, {{get:()=>val, configurable:true}}) }} catch(e){{}} }};
  def(navigator, 'userAgent',            '{fp.user_agent}');
  def(navigator, 'platform',             '{fp.platform}');
  def(navigator, 'hardwareConcurrency',  {fp.hardware_concurrency});
  def(navigator, 'deviceMemory',         {fp.device_memory});
  def(navigator, 'languages',            {langs});
  def(navigator, 'language',             '{fp.languages[0]}');
  def(navigator, 'maxTouchPoints',       5);
  def(screen, 'width',       {fp.screen_width});
  def(screen, 'height',      {fp.screen_height});
  def(screen, 'availWidth',  {fp.screen_width});
  def(screen, 'availHeight', {fp.screen_height});

  const gpProxy = {{ apply(t, ctx, args) {{
    if (args[0]===37445) return '{fp.webgl_vendor}';
    if (args[0]===37446) return '{fp.webgl_renderer}';
    return Reflect.apply(t,ctx,args);
  }} }};
  try {{ WebGLRenderingContext.prototype.getParameter = new Proxy(WebGLRenderingContext.prototype.getParameter, gpProxy); }} catch(e){{}}
  try {{ WebGL2RenderingContext.prototype.getParameter = new Proxy(WebGL2RenderingContext.prototype.getParameter, gpProxy); }} catch(e){{}}

  const n = {fp.canvas_noise};
  const origTDU = HTMLCanvasElement.prototype.toDataURL;
  HTMLCanvasElement.prototype.toDataURL = function(t,...a) {{
    const ctx = this.getContext('2d');
    if(ctx){{ const d=ctx.getImageData(0,0,this.width||1,this.height||1); for(let i=0;i<d.data.length;i+=4){{ d.data[i]^=Math.floor(n*10)&1; }} ctx.putImageData(d,0,0); }}
    return origTDU.apply(this,[t,...a]);
  }};

  try {{ Object.defineProperty(window,'RTCPeerConnection',{{value:undefined}}); }} catch(e){{}}
  if(!window.chrome) window.chrome = {{runtime:{{}}}};
}})();
"""

    def _navigate(self, *_):
        url = self.url_field.text.strip()
        if not url.startswith("http"):
            url = "https://" + url
        MDSnackbar(MDSnackbarText(text=f"Navigating to {url}")).open()

    def _quick_nav(self, url):
        self.url_field.text = url
        self._navigate()

    def _regen_fp(self, *_):
        if self.profile:
            manager.regen_fingerprint(self.profile.id)
            self.load_profile(self.profile.id)
            MDSnackbar(MDSnackbarText(text="Fingerprint regenerated!")).open()

    def _go_back(self, *_):
        self.manager.current = "profiles"


# ────────────────────────────────────────────────────────────────
#  Fingerprint Inspector Screen
# ────────────────────────────────────────────────────────────────
class FingerprintScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation="vertical")

        bar  = MDTopAppBar(type="small")
        leading = MDTopAppBarLeadingButtonContainer()
        back_btn = MDIconButton(icon="arrow-left", on_release=lambda *_: setattr(self.manager, 'current', 'profiles'))
        leading.add_widget(back_btn)
        bar.add_widget(leading)
        bar.add_widget(MDTopAppBarTitle(text="Fingerprint Details"))
        root.add_widget(bar)

        scroll = MDScrollView()
        self.box = MDBoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(8),
            size_hint_y=None,
        )
        self.box.bind(minimum_height=self.box.setter("height"))
        scroll.add_widget(self.box)
        root.add_widget(scroll)
        self.add_widget(root)

    def load(self, pid):
        self.box.clear_widgets()
        p  = manager.get(pid)
        if not p: return
        fp = p.fingerprint

        rows = [
            ("Profile",   p.name),
            ("OS Type",   fp.os_type.title()),
            ("Device",    f"{fp.device_brand} {fp.device_model}"),
            ("Screen",    f"{fp.screen_width} x {fp.screen_height} @ {fp.device_pixel_ratio}x DPR"),
            ("User Agent", fp.user_agent[:60] + "..."),
            ("Platform",  fp.platform),
            ("Timezone",  fp.timezone),
            ("Language",  ", ".join(fp.languages)),
            ("CPU Cores", str(fp.hardware_concurrency)),
            ("RAM",       f"{fp.device_memory} GB"),
            ("WebGL Vendor",   fp.webgl_vendor),
            ("WebGL Renderer", fp.webgl_renderer),
            ("Canvas Noise",   str(fp.canvas_noise)),
            ("Audio Noise",    str(fp.audio_noise)),
            ("Proxy",     p.proxy_url() or "None"),
        ]

        for label, value in rows:
            card = MDCard(
                orientation="vertical",
                padding=[dp(12), dp(8)],
                radius=[8],
                size_hint_y=None, height=dp(56),
            )
            card.add_widget(MDLabel(text=label, theme_text_color="Secondary",
                                    font_style="Label", role="small",
                                    size_hint_y=None, height=dp(18)))
            card.add_widget(MDLabel(text=value, bold=True,
                                    font_style="Body", role="medium",
                                    size_hint_y=None, height=dp(22)))
            self.box.add_widget(card)


# ────────────────────────────────────────────────────────────────
#  Main App
# ────────────────────────────────────────────────────────────────
class StealthBrowserMobileApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style     = "Dark"
        self.title = "StealthBrowser Mobile"

        sm = MDScreenManager()
        sm.add_widget(ProfileListScreen(name="profiles"))
        sm.add_widget(CreateProfileScreen(name="create"))
        sm.add_widget(BrowserScreen(name="browser"))
        sm.add_widget(FingerprintScreen(name="fingerprint"))
        return sm

    def on_start(self):
        pass


if __name__ == "__main__":
    StealthBrowserMobileApp().run()
