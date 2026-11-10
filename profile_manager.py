"""
StealthBrowser Mobile - Profile Manager
"""
import json, uuid, shutil
from datetime import datetime
from pathlib import Path
from fingerprints import MobileFingerprint, MobileFingerprintEngine

PROFILES_DIR  = Path(__file__).parent / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)
MAX_PROFILES  = 10
engine        = MobileFingerprintEngine()


class MobileProfile:
    def __init__(self, name, proxy=None, os_type="android",
                 fingerprint=None, profile_id=None,
                 created_at=None, notes="", last_used=None):
        self.id          = profile_id or str(uuid.uuid4())[:8]
        self.name        = name
        self.proxy       = proxy or {}
        self.os_type     = os_type
        self.fingerprint = fingerprint or engine.generate(os_type)
        self.created_at  = created_at or datetime.now().isoformat()
        self.last_used   = last_used
        self.notes       = notes

    @property
    def config_path(self):
        return PROFILES_DIR / self.id / "profile.json"

    @property
    def cookies_path(self):
        d = PROFILES_DIR / self.id / "cookies"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "id": self.id, "name": self.name, "proxy": self.proxy,
            "os_type": self.os_type,
            "fingerprint": self.fingerprint.to_dict(),
            "created_at": self.created_at,
            "last_used": self.last_used, "notes": self.notes,
        }
        self.config_path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, pid):
        path = PROFILES_DIR / pid / "profile.json"
        data = json.loads(path.read_text())
        fp   = MobileFingerprint.from_dict(data.pop("fingerprint"))
        return cls(fingerprint=fp, **data)

    def delete(self):
        shutil.rmtree(PROFILES_DIR / self.id, ignore_errors=True)

    def mark_used(self):
        self.last_used = datetime.now().isoformat()
        self.save()

    def proxy_url(self):
        p = self.proxy
        if not p.get("host"): return None
        auth = f"{p['user']}:{p['pass']}@" if p.get("user") else ""
        return f"{p.get('type','http')}://{auth}{p['host']}:{p.get('port','')}"


class ProfileManager:
    def list(self):
        ps = []
        for d in PROFILES_DIR.iterdir():
            if d.is_dir() and (d / "profile.json").exists():
                try: ps.append(MobileProfile.load(d.name))
                except: pass
        return sorted(ps, key=lambda x: x.created_at, reverse=True)

    def count(self): return len(self.list())
    def is_full(self): return self.count() >= MAX_PROFILES

    def create(self, name, proxy=None, os_type="android", notes=""):
        if self.is_full():
            raise ValueError(f"Max {MAX_PROFILES} profiles reached!")
        p = MobileProfile(name=name, proxy=proxy, os_type=os_type, notes=notes)
        p.save()
        return p

    def get(self, pid):
        try: return MobileProfile.load(pid)
        except: return None

    def delete(self, pid):
        p = self.get(pid)
        if p: p.delete()

    def regen_fingerprint(self, pid):
        p = self.get(pid)
        if p:
            p.fingerprint = engine.generate(p.os_type)
            p.save()
        return p
