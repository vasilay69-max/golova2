[app]
title = Голова под контролем
package.name = headache
package.domain = ru.student

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1
requirements = python3==3.12.0,hostpython3==3.12.0,kivy,sqlite3

android.accept_sdk_license = True
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0
