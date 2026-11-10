[app]
title = StealthBrowser
package.name = stealthbrowser
package.domain = com.stealth
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

requirements = python3,kivy==2.3.2,kivymd,requests,pillow,playwright

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.api = 34
android.minapi = 26
android.ndk = 25c
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
