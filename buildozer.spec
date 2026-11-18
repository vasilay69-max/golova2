[app]
title = Голова под контролем
package.name = headache
package.domain = ru.student

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1

# Фиксируем одинаковую версию для сборки и приложения.
# Python 3.11 — стабильная связка с Buildozer и Kivy 2.3.1.
requirements = python3==3.11.16,hostpython3==3.11.16,kivy==2.3.1,sqlite3

# Автоматически принимаем лицензии Android SDK.
android.accept_sdk_license = True

# Проверенная версия NDK: в r28c есть конфликт с grpmodule.c в Python 3.12,
# 27c стабильно собирается с Python 3.11.
android.ndk = 27c
android.api = 33
android.minapi = 24

# Используем стабильную ветку python-for-android.
p4a.branch = master

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 0
