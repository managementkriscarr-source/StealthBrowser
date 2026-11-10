"""
StealthBrowser Mobile - Fingerprint Engine
Mobile-optimized fingerprints (Android/iOS UAs)
"""
import random
import json
from dataclasses import dataclass, asdict


ANDROID_UAS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.102 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S926B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.69 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; OnePlus 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Redmi Note 12 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.102 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-F946B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; POCO F5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.69 Mobile Safari/537.36",
]

IOS_UAS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
]

ANDROID_DEVICES = [
    {"brand": "Samsung", "model": "SM-S918B", "screen": (1080, 2340), "dpr": 3.0},
    {"brand": "Google",  "model": "Pixel 8 Pro", "screen": (1344, 2992), "dpr": 3.5},
    {"brand": "Samsung", "model": "SM-A546B", "screen": (1080, 2316), "dpr": 2.0},
    {"brand": "OnePlus", "model": "OP594BL1", "screen": (1440, 3216), "dpr": 3.0},
    {"brand": "Xiaomi",  "model": "Redmi Note 12 Pro", "screen": (1080, 2400), "dpr": 2.75},
    {"brand": "Google",  "model": "Pixel 9", "screen": (1080, 2424), "dpr": 2.625},
    {"brand": "Samsung", "model": "SM-S926B", "screen": (1080, 2340), "dpr": 3.0},
]

TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Denver",
    "America/Los_Angeles", "America/Phoenix", "America/Detroit",
]

LANGUAGES = [["en-US", "en"], ["en-US"], ["en-US", "en-GB", "en"]]

WEBGL_MOBILE = [
    ("Qualcomm", "Adreno (TM) 740"),
    ("Qualcomm", "Adreno (TM) 730"),
    ("ARM",      "Mali-G715"),
    ("ARM",      "Mali-G77 MC9"),
    ("Apple",    "Apple GPU"),
    ("Imagination Technologies", "PowerVR Series6XT"),
]

CPU_CORES_MOBILE = [4, 6, 8]
MEMORY_MOBILE    = [4, 6, 8, 12]


@dataclass
class MobileFingerprint:
    user_agent: str
    device_brand: str
    device_model: str
    screen_width: int
    screen_height: int
    device_pixel_ratio: float
    timezone: str
    languages: list
    webgl_vendor: str
    webgl_renderer: str
    hardware_concurrency: int
    device_memory: int
    canvas_noise: float
    audio_noise: float
    platform: str
    os_type: str  # android | ios

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class MobileFingerprintEngine:
    def __init__(self):
        self._used_noises = set()

    def generate(self, os_type: str = "android") -> MobileFingerprint:
        canvas_noise = round(random.uniform(0.001, 0.999), 6)
        while canvas_noise in self._used_noises:
            canvas_noise = round(random.uniform(0.001, 0.999), 6)
        self._used_noises.add(canvas_noise)

        wgl_v, wgl_r = random.choice(WEBGL_MOBILE)

        if os_type == "ios":
            ua      = random.choice(IOS_UAS)
            device  = {"brand": "Apple", "model": "iPhone", "screen": (390, 844), "dpr": 3.0}
            platform = "iPhone"
        else:
            ua      = random.choice(ANDROID_UAS)
            device  = random.choice(ANDROID_DEVICES)
            platform = "Linux armv8l"

        return MobileFingerprint(
            user_agent=ua,
            device_brand=device["brand"],
            device_model=device["model"],
            screen_width=device["screen"][0],
            screen_height=device["screen"][1],
            device_pixel_ratio=device["dpr"],
            timezone=random.choice(TIMEZONES),
            languages=random.choice(LANGUAGES),
            webgl_vendor=wgl_v,
            webgl_renderer=wgl_r,
            hardware_concurrency=random.choice(CPU_CORES_MOBILE),
            device_memory=random.choice(MEMORY_MOBILE),
            canvas_noise=canvas_noise,
            audio_noise=round(random.uniform(0.0001, 0.0009), 7),
            platform=platform,
            os_type=os_type,
        )
