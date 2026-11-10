[app]
title = StealthBrowser
package.name = stealthbrowser
package.domain = com.stealth
source.dir = .
source.include_exts = py,png,jpg,kv,json
version = 1.0

# Playwright cannot run on Android ARM; only pure python & kivy modules needed
requirements = python3,kivy==2.3.2,pillow,requests

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
