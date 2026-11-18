[app]
title = Голова под контролем
package.name = headache
package.domain = ru.student

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1
# Жёстко фиксируем версию Python и для сборки, и для приложения
requirements = python3==3.12.0,hostpython3==3.12.0,kivy==2.3.1,sqlite3

# Автоматически принимаем лицензии Android SDK
android.accept_sdk_license = True

# Стабильная ветка python-for-android для Python 3.12
p4a.branch = master

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0
