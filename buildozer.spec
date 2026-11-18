[app]
title = Голова под контролем
package.name = headache
package.domain = ru.student
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 0.1
requirements = python3==3.10.9,hostpython3==3.10.9,kivy==2.3.1,sqlite3
android.accept_sdk_license = True
android.ndk = 27c
android.api = 33
android.minapi = 24
p4a.branch = master
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0
