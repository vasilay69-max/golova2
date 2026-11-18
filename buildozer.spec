[app]
title = Голова под контролем
package.name = headache
package.domain = ru.student

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1
requirements = python3,kivy,sqlite3

# Автоматически принимать лицензии Android SDK
android.accept_sdk_license = True

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0
