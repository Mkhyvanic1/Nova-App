[app]
title = Nova
package.name = novaapp
package.domain = org.mpalanyi
source.dir = .
source.include_exts = py,png,jpg,jpeg,json
version = 1.0
requirements = python3,kivy,requests,plyer,pyjnius
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,BATTERY_STATS,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,RECORD_AUDIO

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
