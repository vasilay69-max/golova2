#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Голова под контролем — мобильное приложение на Python + Kivy + SQLite.
Обновлённый дизайн: карточки, цветовые акценты, разделы формы, динамика,
сводка для врача, помощь при мигрени.
Запуск на Windows: pip install kivy && python main.py
Сборка APK: buildozer -v android debug
"""

import os
import sqlite3
import datetime as dt
import random

from kivy.app import App
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ============================ ПАЛИТРА ============================
BG = (0.957, 0.965, 0.984, 1)
CARD = (1, 1, 1, 1)
INK = (0.122, 0.165, 0.267, 1)
MUTED = (0.42, 0.463, 0.565, 1)
ACC = (0.184, 0.357, 0.918, 1)
LINE = (0.875, 0.898, 0.945, 1)
GOOD = (0.122, 0.616, 0.42, 1)
WARN = (0.84, 0.6, 0.0, 1)
BAD = (0.839, 0.271, 0.271, 1)
LIGHT = (0.916, 0.941, 0.996, 1)

CAUSES = ["Недосып", "Стресс", "Погода", "Голод", "Алкоголь",
          "Кофеин", "Яркий свет", "Шум", "Физическая нагрузка",
          "Духота", "Долго за экраном", "Менструация"]

HELP_TEXT = """ЧТО ДЕЛАТЬ В НАЧАЛЕ ПРИСТУПА
• Нажмите «Приступ начался»: время запишется точно. Когда боль пройдёт, нажмите «Приступ закончился».
• Если врач назначил препарат, его обычно советуют принять в самом начале боли. Дозу и частоту определяет врач.
• Лягте в тихой затемнённой комнате, приложите прохладный компресс.
• Выпейте воды. Не пропускайте еду: голод усиливает боль.
• Уберите экран, яркий свет и резкие запахи.

СРОЧНО ВЫЗЫВАЙТЕ СКОРУЮ (103 или 112):
• боль возникла внезапно и самая сильная в жизни;
• боль после удара или травмы головы;
• слабость, онемение, перекос лица, нарушение речи, потеря зрения;
• высокая температура, сыпь, скованность шеи;
• спутанность сознания, судороги, обморок;
• давление 180/120 и выше с сильной головной болью.

СТОИТ ПОКАЗАТЬСЯ ВРАЧУ В БЛИЖАЙШИЕ ДНИ:
• боль впервые после 50 лет или резко изменилась;
• приступы стали чаще или сильнее;
• обезболивающие нужны 10+ дней в месяц;
• аура длится дольше часа или стала другой;
• приступы мешают работе, учёбе, обычной жизни.

ЧТО ПОМОГАЕТ РЕЖЕ БОЛЕТЬ
• Ложитесь и вставайте в одно время, в том числе в выходные.
• Не пропускайте еду, пейте воду.
• Ограничьте алкоголь и кофеин. Отмечайте причины: так видно, что повторяется.
• Умеренная нагрузка и перерывы в работе с экраном.
• Покажите врачу сводку: кнопка внизу этой вкладки.

Памятка не заменяет консультацию врача."""


# ============================ ХЕЛПЕРЫ ============================
def show_message(text, title="Сообщение"):
    box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
    lab = Label(text=text, halign="center", valign="middle")
    lab.bind(size=lambda inst, val: setattr(lab, "text_size", val))
    box.add_widget(lab)
    btn = Button(text="OK", size_hint_y=None, height=dp(44))
    pop = Popup(title=title, content=box, size_hint=(0.9, 0.4))
    btn.bind(on_release=pop.dismiss)
    box.add_widget(btn)
    pop.open()


def fmt_ru(iso):
    if not iso:
        return ""
    try:
        d = dt.date.fromisoformat(iso)
    except Exception:
        return iso
    months = ["января", "февраля", "марта", "апреля", "мая", "июня",
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    return f"{d.day} {months[d.month - 1]} {d.year}"


def calc_dur(start, end):
    a = dt.datetime.strptime(start, "%H:%M")
    b = dt.datetime.strptime(end, "%H:%M")
    return int((b - a).total_seconds() // 60) % 1440


def dur_text(m):
    if m >= 60:
        return f"{m // 60} ч {m % 60:02d} мин"
    return f"{m} мин"


def bp_str(s, d):
    return f"{round(s)}/{round(d)}"


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


# ======================= КАСТОМНЫЕ ВИДЖЕТЫ =======================
class Card(BoxLayout):
    """Белая карточка с цветной полосой слева; цвет фона и полосы меняется."""

    def __init__(self, bg=CARD, strip=None, padding=dp(14), **kw):
        super().__init__(orientation="vertical", padding=padding,
                         spacing=dp(6), **kw)
        with self.canvas.before:
            self._c_bg = Color(*bg)
            self._r_bg = Rectangle(pos=self.pos, size=self.size)
            self._c_st = Color(*(strip or bg))
            self._r_st = Rectangle(pos=self.pos, size=(dp(6), self.height))
        self.bind(pos=self._upd, size=self._upd)

    def set_colors(self, bg, strip=None):
        self._c_bg.rgba = bg
        self._c_st.rgba = strip or bg

    def _upd(self, *a):
        self._r_bg.pos = self.pos
        self._r_bg.size = self.size
        self._r_st.pos = self.pos
        self._r_st.size = (dp(6), self.height)


class ChartWidget(Widget):
    """Простой график: давление — линии, боль — столбики, шкалы по краям."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.series = {}
        self.bind(pos=self._draw, size=self._draw)

    def set_series(self, series):
        self.series = series
        self._draw()

    def _draw(self, *a):
        self.canvas.clear()
        w, h = self.width, self.height
        if w < 40 or h < 40:
            return
        L, R, T, B = dp(36), dp(36), dp(14), dp(26)
        with self.canvas:
            Color(*CARD)
            Rectangle(pos=self.pos, size=self.size)
            Color(*LINE)
            Line(rectangle=(self.x + L, self.y + B,
                            w - L - R, h - T - B), width=1)
            # Сетка давления
            for v in (80, 120, 160):
                y = self.y + B + (h - T - B) * (1 - (v - 60) / 120)
                Color(*LINE)
                Line(points=[self.x + L, y, self.x + w - R, y], width=1)
            if not self.series:
                return
            days = sorted(self.series.keys())[-30:]
            n = len(days)
            if n < 2:
                return
            X = lambda i: self.x + L + (w - L - R) * (i + 0.5) / n
            Yp = lambda v: self.y + B + (h - T - B) * (1 - (v - 60) / 120)
            Yb = lambda v: self.y + B + (h - T - B) * (1 - v / 10)
            # Столбики боли
            Color(*BAD[:3], 0.25)
            bw = max(2, (w - L - R) / n * 0.32)
            for i, k in enumerate(days):
                pain = self.series[k].get("pain")
                if pain is not None:
                    y = Yb(pain)
                    Rectangle(pos=(X(i) - bw, self.y + B),
                              size=(bw * 2, y - self.y - B))
            # Линии давления
            for key, col in (("sys", ACC), ("dia", (0.075, 0.643, 0.643, 1))):
                Color(*col)
                pts = []
                for i, k in enumerate(days):
                    v = self.series[k].get(key)
                    if v is not None:
                        pts += [X(i), Yp(v)]
                if len(pts) >= 4:
                    Line(points=pts, width=dp(2))


# ============================= БАЗА =============================
class Database:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init()

    def _init(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL, type TEXT NOT NULL,
                intensity INTEGER, side TEXT, duration_min INTEGER,
                aura INTEGER DEFAULT 0, effort INTEGER DEFAULT 0,
                nausea INTEGER DEFAULT 0, medication TEXT, note TEXT,
                bp_sys INTEGER, bp_dia INTEGER
            );
            CREATE TABLE IF NOT EXISTS triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS episode_triggers (
                episode_id INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
                trigger_id INTEGER REFERENCES triggers(id),
                PRIMARY KEY (episode_id, trigger_id)
            );
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT, dob TEXT
            );
            CREATE TABLE IF NOT EXISTS active (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                date TEXT, time TEXT
            );
        """)
        for n in CAUSES:
            c.execute("INSERT OR IGNORE INTO triggers(name) VALUES (?)", (n,))
        self.conn.commit()

    def add_episode(self, d, trig_ids):
        c = self.conn.cursor()
        c.execute("""INSERT INTO episodes
            (ts, type, intensity, side, duration_min, aura, effort,
             nausea, medication, note, bp_sys, bp_dia)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (d["ts"], d["type"], d["intensity"], d["side"],
                   d["duration_min"], d["aura"], d["effort"], d["nausea"],
                   d["medication"], d["note"], d.get("bp_sys"), d.get("bp_dia")))
        ep_id = c.lastrowid
        for tid in trig_ids:
            c.execute("INSERT INTO episode_triggers(episode_id, trigger_id) "
                      "VALUES (?, ?)", (ep_id, tid))
        self.conn.commit()
        return ep_id

    def delete_episode(self, ep_id):
        self.conn.execute("DELETE FROM episodes WHERE id = ?", (ep_id,))
        self.conn.commit()

    def get_episodes(self, limit=500):
        return self.conn.execute("""
            SELECT e.*, GROUP_CONCAT(t.name, ', ') AS triggers
            FROM episodes e
            LEFT JOIN episode_triggers et ON et.episode_id = e.id
            LEFT JOIN triggers t ON t.id = et.trigger_id
            GROUP BY e.id ORDER BY e.ts DESC LIMIT ?
        """, (limit,)).fetchall()

    def get_triggers(self):
        return self.conn.execute(
            "SELECT * FROM triggers ORDER BY name").fetchall()

    def add_trigger(self, name):
        self.conn.execute("INSERT OR IGNORE INTO triggers(name) VALUES (?)",
                          (name,))
        self.conn.commit()
        return self.conn.execute(
            "SELECT id FROM triggers WHERE name = ?",
            (name,)).fetchone()["id"]

    def stats(self):
        return self.conn.execute("""
            SELECT COUNT(*) AS n, AVG(intensity) AS avg_int,
                   AVG(duration_min) AS avg_dur,
                   SUM(CASE WHEN medication != '' THEN 1 ELSE 0 END) AS with_med
            FROM episodes
        """).fetchone()

    def trigger_analysis(self):
        total = self.conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        rows = self.conn.execute("""
            SELECT t.name, COUNT(DISTINCT et.episode_id) AS cnt
            FROM triggers t
            LEFT JOIN episode_triggers et ON et.trigger_id = t.id
            GROUP BY t.id ORDER BY cnt DESC
        """).fetchall()
        return [(r["name"], r["cnt"], total,
                 r["cnt"] / total if total else 0) for r in rows]

    def bp_readings(self, day):
        out = []
        for e in self.conn.execute(
                "SELECT ts, bp_sys, bp_dia FROM episodes "
                "WHERE substr(ts, 1, 10) = ? AND bp_sys IS NOT NULL",
                (day,)).fetchall():
            out.append((e["ts"][11:16], e["bp_sys"], e["bp_dia"]))
        return sorted(out)

    def bp_summary(self):
        days = [r["d"] for r in self.conn.execute(
            "SELECT DISTINCT substr(ts, 1, 10) AS d FROM episodes "
            "WHERE bp_sys IS NOT NULL ORDER BY d DESC LIMIT 30").fetchall()]
        if not days:
            return "Давление: измерений пока нет."
        last_day = days[0]
        t, s, d = self.bp_readings(last_day)[-1]
        s_txt = f"Последнее давление: {bp_str(s, d)} ({fmt_ru(last_day)}"
        s_txt += f" в {t})" if t else ")"
        week = []
        for i in range(7):
            k = (dt.date.today() - dt.timedelta(days=i)).isoformat()
            week += self.bp_readings(k)
        if week:
            s_txt += f"\nСреднее за 7 дней: {bp_str(_mean([x[1] for x in week]), _mean([x[2] for x in week]))}"
        return s_txt

    def daily_series(self):
        d = {}
        for e in self.get_episodes(limit=2000):
            day = e["ts"][:10]
            x = d.setdefault(day, {"sys": [], "dia": [], "pain": []})
            x["pain"].append(e["intensity"])
            if e["bp_sys"] and e["bp_dia"]:
                x["sys"].append(e["bp_sys"])
                x["dia"].append(e["bp_dia"])
        return {k: {"sys": _mean(v["sys"]), "dia": _mean(v["dia"]),
                    "pain": max(v["pain"]) if v["pain"] else None}
                for k, v in sorted(d.items())}

    def set_active(self, date=None, time=None):
        self.conn.execute("DELETE FROM active")
        if date:
            self.conn.execute("INSERT INTO active(id, date, time) "
                              "VALUES (1, ?, ?)", (date, time))
        self.conn.commit()

    def get_active(self):
        r = self.conn.execute("SELECT * FROM active WHERE id = 1").fetchone()
        return dict(r) if r else None

    def set_profile(self, name, dob):
        self.conn.execute("INSERT OR REPLACE INTO profile(id, name, dob) "
                          "VALUES (1, ?, ?)", (name, dob))
        self.conn.commit()

    def get_profile(self):
        r = self.conn.execute("SELECT name, dob FROM profile WHERE id = 1"
                              ).fetchone()
        return dict(r) if r else {"name": "", "dob": ""}

    def summary_7d(self):
        today = dt.date.today()
        def rng(a, b):
            return [(today - dt.timedelta(days=i)).isoformat()
                    for i in range(a, b + 1)]
        cur = rng(0, 6)
        prev = rng(7, 13)
        ser = self.daily_series()
        def pain(days):
            vals = [ser[k]["pain"] for k in days if k in ser
                    and ser[k]["pain"] is not None]
            return _mean(vals)
        def count(days):
            return sum(1 for e in self.get_episodes()
                       if e["ts"][:10] in days)
        f = lambda v: f"{v:.1f}" if v is not None else "—"
        return (f"Боль 0–10: {f(pain(prev))} → {f(pain(cur))}\n"
                f"Приступов: {count(prev)} → {count(cur)}")

    def advice(self):
        tips = []
        eps = self.get_episodes(limit=2000)
        last = [e for e in eps
                if e["ts"][:10] > (dt.date.today()
                                   - dt.timedelta(days=8)).isoformat()]
        hi = [e for e in last if e["bp_sys"] and
              (e["bp_sys"] >= 140 or (e["bp_dia"] or 0) >= 90)]
        if len(hi) >= 2:
            tips.append(f"Давление 140/90+ в {len(hi)} эпизодах за неделю — "
                        "покажите записи терапевту.")
        trg = {}
        for e in eps:
            for t in (e["triggers"] or "").split(", "):
                if t:
                    trg[t] = trg.get(t, 0) + 1
        if trg:
            top = max(trg.items(), key=lambda kv: kv[1])
            if top[1] >= 3:
                tips.append(f"Чаще всего приступы совпадают с фактором "
                            f"«{top[0]}» ({top[1]} раз).")
        if not tips:
            tips.append("Пока недостаточно данных. Вносите записи, "
                        "и здесь появятся подсказки.")
        return "\n".join("• " + t for t in tips)


# ============================= ЭКРАНЫ =============================
class MainScreen(Screen):
    def __init__(self, db, **kw):
        super().__init__(**kw)
        self.db = db
        root = BoxLayout(orientation="vertical", padding=dp(10),
                         spacing=dp(8))
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(self._bg, "pos", root.pos),
                  size=lambda *a: setattr(self._bg, "size", root.size))

        # Заголовок
        hdr = BoxLayout(size_hint_y=None, height=dp(38))
        hdr.add_widget(Label(text="Голова под контролем", bold=True,
                             font_size="20sp", color=INK))
        hdr.add_widget(Label(text=fmt_ru(dt.date.today().isoformat()),
                             color=MUTED, size_hint_x=None, width=dp(120)))
        root.add_widget(hdr)

        # Карточка прогноза риска
        self.risk_card = Card(bg=LIGHT, strip=ACC)
        self.risk_card.size_hint_y = None
        self.risk_card.height = dp(110)
        self.risk_head = Label(text="Прогноз", bold=True, font_size="15sp",
                               color=INK, size_hint_y=None, height=dp(24))
        self.risk_body = Label(text="Погода не подключена",
                               color=INK, font_size="12sp")
        self.risk_card.add_widget(self.risk_head)
        self.risk_card.add_widget(self.risk_body)
        root.add_widget(self.risk_card)

        # Карточка давления
        bp_card = Card(bg=CARD, strip=LINE)
        bp_card.size_hint_y = None
        bp_card.height = dp(80)
        bp_card.add_widget(Label(text="ДАВЛЕНИЕ", color=MUTED,
                                 font_size="10sp", size_hint_y=None,
                                 height=dp(18), halign="left"))
        self.bp_label = Label(text="—", color=INK, bold=True, font_size="13sp",
                              halign="left")
        bp_card.add_widget(self.bp_label)
        root.add_widget(bp_card)

        # Заголовок истории и кнопка добавить
        act = BoxLayout(size_hint_y=None, height=dp(38))
        act.add_widget(Label(text="История приступов", bold=True,
                             font_size="15sp", color=INK, halign="left"))
        add_btn = Button(text="+ Записать приступ", size_hint_x=None,
                         width=dp(180), background_color=ACC)
        add_btn.bind(on_release=lambda *a: setattr(
            self.manager, "current", "new"))
        act.add_widget(add_btn)
        root.add_widget(act)

        # Шапка таблицы
        head = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(4))
        for txt, wdt in (("Дата", 0.32), ("Характер", 0.22),
                         ("Боль", 0.14), ("Длит.", 0.16), ("Давл.", 0.16)):
            head.add_widget(Label(text=txt, bold=True, font_size="11sp",
                                  color=MUTED,
                                  size_hint_x=wdt))
        root.add_widget(head)

        # Сама таблица
        scroll = ScrollView()
        self.table = BoxLayout(orientation="vertical", size_hint_y=None,
                               spacing=dp(2))
        self.table.bind(minimum_height=self.table.setter("height"))
        scroll.add_widget(self.table)
        root.add_widget(scroll)

        # Кнопки
        bottom = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        for txt, target in (("Анализ", "analysis"),
                            ("Динамика", "dynamic"),
                            ("Помощь", "help"),
                            ("Отчёт", "report")):
            b = Button(text=txt)
            b.bind(on_release=lambda *a, t=target:
                   setattr(self.manager, "current", t))
            bottom.add_widget(b)
        root.add_widget(bottom)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.refresh()
        return True

    def refresh(self):
        # Цвет карточки по риску (пока — без погоды, ставим «нейтрально»)
        self.risk_card.set_colors(LIGHT, ACC)
        self.risk_head.text = "Прогноз по погоде"
        self.risk_body.text = ("Подключите погоду, чтобы получать "
                               "предупреждения о приступе.")
        self.bp_label.text = self.db.bp_summary()

        self.table.clear_widgets()
        eps = self.db.get_episodes()
        if not eps:
            self.table.add_widget(Label(
                text="Приступов пока нет.\nНажмите «+ Записать приступ».",
                color=MUTED, size_hint_y=None, height=dp(90),
                halign="center"))
            return
        for e in eps:
            row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(4))
            # цветная полоска-уровень
            color = (0.99, 0.91, 0.91, 1) if e["intensity"] >= 7 \
                else (1, 0.96, 0.86, 1) if e["intensity"] >= 4 \
                else (0.94, 0.97, 1, 1)
            with row.canvas.before:
                Color(*color)
                r = Rectangle(pos=row.pos, size=row.size)
            row.bind(pos=lambda inst, val, rect=r: setattr(rect, "pos", val),
                     size=lambda inst, val, rect=r: setattr(rect, "size", val))
            day = ".".join(reversed(e["ts"][:10].split("-")))
            tm = e["ts"][11:16]
            bpd = f'{e["bp_sys"]}/{e["bp_dia"]}' \
                if e["bp_sys"] and e["bp_dia"] else "—"
            for txt, wdt in ((f"{day}\n{tm}", 0.32),
                             (e["type"][:10], 0.22),
                             (f'{e["intensity"]}/10', 0.14),
                             (dur_text(e["duration_min"] or 0), 0.16),
                             (bpd, 0.16)):
                row.add_widget(Label(text=txt, font_size="11sp",
                                     size_hint_x=wdt, color=INK))
            self.table.add_widget(row)


class NewEpisodeScreen(Screen):
    def __init__(self, db, **kw):
        super().__init__(**kw)
        self.db = db
        outer = BoxLayout(orientation="vertical", padding=dp(8),
                          spacing=dp(6))

        hdr = BoxLayout(size_hint_y=None, height=dp(38))
        back = Button(text="← Назад", size_hint_x=None, width=dp(90))
        back.bind(on_release=lambda *a: setattr(
            self.manager, "current", "main"))
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Новый приступ", bold=True,
                             font_size="16sp", color=INK))
        outer.add_widget(hdr)

        scroll = ScrollView()
        form = BoxLayout(orientation="vertical", size_hint_y=None,
                         spacing=dp(10))
        form.bind(minimum_height=form.setter("height"))

        def section(title):
            b = BoxLayout(orientation="vertical", size_hint_y=None,
                          spacing=dp(4))
            b.add_widget(Label(text=title, bold=True, color=ACC,
                               size_hint_y=None, height=dp(24),
                               halign="left", font_size="13sp"))
            box = BoxLayout(orientation="vertical", size_hint_y=None,
                            spacing=dp(4))
            box.bind(minimum_height=box.setter("height"))
            b.add_widget(box)
            form.add_widget(b)
            return box

        def field(label, widget, height=44):
            row = BoxLayout(size_hint_y=None, height=dp(height),
                            spacing=dp(6))
            row.add_widget(Label(text=label, color=INK, halign="left",
                                 size_hint_x=0.42, font_size="12sp"))
            row.add_widget(widget)
            return row

        # --- Когда
        s = section("Когда")
        now = dt.datetime.now()
        self.date_input = TextInput(text=dt.date.today().isoformat(),
                                    multiline=False, size_hint_y=None,
                                    height=dp(40), font_size="13sp")
        s.add_widget(field("Дата (ГГГГ-ММ-ДД)", self.date_input))
        self.time_input = TextInput(text=now.strftime("%H:%M"),
                                    multiline=False, size_hint_y=None,
                                    height=dp(40), font_size="13sp")
        s.add_widget(field("Начало (ЧЧ:ММ)", self.time_input))
        self.end_input = TextInput(
            text=(now + dt.timedelta(minutes=30)).strftime("%H:%M"),
            multiline=False, size_hint_y=None, height=dp(40),
            font_size="13sp")
        s.add_widget(field("Окончание (ЧЧ:ММ)", self.end_input))
        self.dur_label = Label(text="30 мин", color=ACC, bold=True,
                               size_hint_y=None, height=dp(24),
                               halign="left")
        s.add_widget(self.dur_label)

        def upd_dur(*a):
            try:
                d = calc_dur(self.time_input.text, self.end_input.text)
                self.dur_label.text = dur_text(d)
            except Exception:
                self.dur_label.text = "—"
        self.time_input.bind(text=upd_dur)
        self.end_input.bind(text=upd_dur)

        # --- Как болело
        s = section("Как болело")
        self.type_sp = Spinner(
            text="Пульсирующая",
            values=["Пульсирующая", "Сжимающая", "Тупая", "Колющая",
                    "Другая"], size_hint_y=None, height=dp(40))
        s.add_widget(field("Характер", self.type_sp))
        self.int_slider = Slider(min=0, max=10, value=5, step=1,
                                 size_hint_y=None, height=dp(40))
        self.int_label = Label(text="5", bold=True, color=ACC,
                               size_hint_x=None, width=dp(50),
                               font_size="15sp")
        int_row = BoxLayout(size_hint_y=None, height=dp(40))
        int_row.add_widget(self.int_slider)
        int_row.add_widget(self.int_label)
        self.int_slider.bind(
            value=lambda inst, val: setattr(
                self.int_label, "text", str(int(val))))
        s.add_widget(field("Интенсивность", int_row))
        self.side_sp = Spinner(
            text="Левая сторона",
            values=["Левая сторона", "Правая сторона", "Двусторонняя",
                    "Другая"], size_hint_y=None, height=dp(40))
        s.add_widget(field("Локализация", self.side_sp))
        self.nausea_sp = Spinner(
            text="Нет", values=["Нет", "Незначительная", "Заметная"],
            size_hint_y=None, height=dp(40))
        s.add_widget(field("Тошнота", self.nausea_sp))

        # --- Что ещё было
        s = section("Что ещё было")
        self.aura_cb = CheckBox(size_hint_x=None, width=dp(40))
        s.add_widget(field("Аура", self.aura_cb))
        self.effort_cb = CheckBox(size_hint_x=None, width=dp(40))
        s.add_widget(field("Усиление при нагрузке", self.effort_cb))

        # --- Возможные причины
        s = section("Возможные причины")
        self.trigger_cbs = {}
        for t in self.db.get_triggers():
            row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
            cb = CheckBox(size_hint_x=None, width=dp(36))
            self.trigger_cbs[t["id"]] = cb
            row.add_widget(cb)
            row.add_widget(Label(text=t["name"], color=INK,
                                 halign="left", font_size="12sp"))
            s.add_widget(row)
        self.new_trigger = TextInput(hint_text="Свой триггер",
                                     multiline=False, size_hint_y=None,
                                     height=dp(40), font_size="13sp")
        s.add_widget(field("Добавить", self.new_trigger))
        add_btn = Button(text="+ в справочник", size_hint_y=None,
                         height=dp(36))
        add_btn.bind(on_release=self.add_trigger)
        s.add_widget(add_btn)

        # --- Давление и лекарство
        s = section("Давление и лекарство")
        bp_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        self.bp_sys = TextInput(text="120", multiline=False,
                                input_filter="int", font_size="13sp")
        self.bp_dia = TextInput(text="80", multiline=False,
                                input_filter="int", font_size="13sp")
        bp_row.add_widget(self.bp_sys)
        bp_row.add_widget(Label(text="/", size_hint_x=None, width=dp(20)))
        bp_row.add_widget(self.bp_dia)
        s.add_widget(field("Давление (верх/низ)", bp_row))
        self.med_input = TextInput(multiline=False, size_hint_y=None,
                                   height=dp(40), font_size="13sp")
        s.add_widget(field("Препараты", self.med_input))
        self.note_input = TextInput(multiline=False, size_hint_y=None,
                                    height=dp(40), font_size="13sp")
        s.add_widget(field("Заметки", self.note_input))

        scroll.add_widget(form)
        outer.add_widget(scroll)

        save_bar = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        hint = Label(text="Длительность и дата считаются сами.",
                     color=MUTED, font_size="11sp", halign="left")
        save_bar.add_widget(hint)
        save_btn = Button(text="Сохранить приступ",
                          background_color=ACC, bold=True)
        save_btn.bind(on_release=self.save)
        save_bar.add_widget(save_btn)
        outer.add_widget(save_bar)
        self.add_widget(outer)

    def add_trigger(self, *a):
        name = self.new_trigger.text.strip()
        if not name:
            show_message("Введите название триггера")
            return
        self.db.add_trigger(name)
        self.new_trigger.text = ""
        show_message(f"Триггер «{name}» добавлен в справочник.")

    def save(self, *a):
        try:
            ts = f"{self.date_input.text.strip()}T{self.time_input.text.strip()}"
            dt.datetime.fromisoformat(ts)
            intensity = int(self.int_slider.value)
            d = {
                "ts": ts, "type": self.type_sp.text,
                "intensity": intensity, "side": self.side_sp.text,
                "duration_min": calc_dur(self.time_input.text.strip(),
                                         self.end_input.text.strip()),
                "aura": int(self.aura_cb.active),
                "effort": int(self.effort_cb.active),
                "nausea": ["Нет", "Незначительная", "Заметная"].index(
                    self.nausea_sp.text),
                "medication": self.med_input.text.strip(),
                "note": self.note_input.text.strip(),
            }
            # Давление — необязательное
            if self.bp_sys.text.strip() and self.bp_dia.text.strip():
                a, b = int(self.bp_sys.text), int(self.bp_dia.text)
                if 60 <= a <= 260 and 30 <= b <= 160 and a > b:
                    d["bp_sys"], d["bp_dia"] = a, b
            trig_ids = [tid for tid, cb in self.trigger_cbs.items()
                        if cb.active]
            self.db.add_episode(d, trig_ids)
            show_message("Эпизод сохранён")
            self.manager.current = "main"
        except Exception as e:
            show_message(f"Ошибка: {e}")


class AnalysisScreen(Screen):
    def __init__(self, db, **kw):
        super().__init__(**kw)
        self.db = db
        root = BoxLayout(orientation="vertical", padding=dp(10),
                         spacing=dp(8))
        hdr = BoxLayout(size_hint_y=None, height=dp(38))
        back = Button(text="← Назад", size_hint_x=None, width=dp(90))
        back.bind(on_release=lambda *a: setattr(
            self.manager, "current", "main"))
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Анализ триггеров", bold=True,
                             font_size="16sp", color=INK))
        root.add_widget(hdr)
        self.content = BoxLayout(orientation="vertical", size_hint_y=None,
                                 spacing=dp(4))
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.content)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self._refresh()
        return True

    def _refresh(self):
        self.content.clear_widgets()
        st = self.db.stats()
        if st["n"] == 0:
            self.content.add_widget(Label(
                text="Данных пока нет.\nДобавьте эпизоды или загрузите демо.",
                color=MUTED, size_hint_y=None, height=dp(80),
                halign="center"))
            b = Button(text="Загрузить демо-данные", size_hint_y=None,
                       height=dp(44))
            b.bind(on_release=self._load_demo)
            self.content.add_widget(b)
            return
        for t in (f"Всего эпизодов: {st['n']}",
                  f"Средняя интенсивность: {st['avg_int']:.1f}/10",
                  f"Средняя длительность: {st['avg_dur']:.0f} мин",
                  f"Эпизодов с препаратами: {st['with_med']}"):
            self.content.add_widget(Label(text=t, color=INK,
                                          size_hint_y=None, height=dp(24),
                                          halign="left"))
        self.content.add_widget(Label(text="Частота триггеров:", bold=True,
                                      color=ACC, size_hint_y=None,
                                      height=dp(30), halign="left"))
        for name, cnt, total, share in self.db.trigger_analysis():
            if cnt == 0:
                continue
            color = GOOD if share < 0.3 else WARN if share < 0.5 else BAD
            row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(6))
            row.add_widget(Label(text=f"{name}: {cnt} из {total}",
                                 color=INK, halign="left", font_size="12sp"))
            row.add_widget(Label(text=f"{share * 100:.0f}%", color=color,
                                 bold=True, size_hint_x=None,
                                 width=dp(70)))
            self.content.add_widget(row)
        self.content.add_widget(Label(
            text="\nЭто статистическая связь, а не доказательство причины.",
            color=MUTED, size_hint_y=None, height=dp(50),
            font_size="11sp"))

    def _load_demo(self, *a):
        names = ["Недосып", "Стресс", "Погода"]
        for _ in range(20):
            days = random.randint(0, 40)
            date = dt.date.today() - dt.timedelta(days=days)
            h = random.randint(9, 20)
            m = random.choice([0, 15, 30, 45])
            ts = f"{date.isoformat()}T{h:02d}:{m:02d}"
            picked = random.sample(names, k=random.randint(0, len(names)))
            ids = [self.db.add_trigger(n) for n in picked]
            self.db.add_episode({
                "ts": ts,
                "type": random.choice(["Пульсирующая", "Сжимающая",
                                       "Тупая"]),
                "intensity": random.randint(3, 9),
                "side": "Левая сторона",
                "duration_min": random.choice([30, 60, 90, 120, 180]),
                "aura": 0, "effort": random.randint(0, 1),
                "nausea": random.randint(0, 2),
                "medication": random.choice(["", "Ибупрофен 400 мг"]),
                "note": "",
                "bp_sys": random.choice([None, 120, 130, 150]),
                "bp_dia": random.choice([None, 80, 85, 95]),
            }, ids)
        self._refresh()


class DynamicScreen(Screen):
    def __init__(self, db, **kw):
        super().__init__(**kw)
        self.db = db
        root = BoxLayout(orientation="vertical", padding=dp(8),
                         spacing=dp(6))
        hdr = BoxLayout(size_hint_y=None, height=dp(38))
        back = Button(text="← Назад", size_hint_x=None, width=dp(90))
        back.bind(on_release=lambda *a: setattr(
            self.manager, "current", "main"))
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Динамика", bold=True, font_size="16sp",
                             color=INK))
        root.add_widget(hdr)
        self.chart = ChartWidget(size_hint_y=None, height=dp(220))
        root.add_widget(self.chart)
        self.text = Label(text="", color=INK, halign="left", valign="top",
                          size_hint_y=None, height=dp(300))
        self.text.bind(size=lambda inst, val:
                       setattr(self.text, "text_size", val))
        scroll = ScrollView()
        wrap = BoxLayout(orientation="vertical", size_hint_y=None,
                         spacing=dp(4))
        wrap.bind(minimum_height=wrap.setter("height"))
        wrap.add_widget(self.text)
        scroll.add_widget(wrap)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self.chart.set_series(self.db.daily_series())
        self.text.text = (self.db.summary_7d() + "\n\n"
                          "ПОДСКАЗКИ\n" + self.db.advice())
        return True


class HelpScreen(Screen):
    def __init__(self, db, **kw):
        super().__init__(**kw)
        self.db = db
        root = BoxLayout(orientation="vertical", padding=dp(8),
                         spacing=dp(6))
        hdr = BoxLayout(size_hint_y=None, height=dp(38))
        back = Button(text="← Назад", size_hint_x=None, width=dp(90))
        back.bind(on_release=lambda *a: setattr(
            self.manager, "current", "main"))
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Помощь при мигрени", bold=True,
                             font_size="16sp", color=INK))
        root.add_widget(hdr)

        card = Card(bg=LIGHT, strip=ACC)
        card.size_hint_y = None
        card.height = dp(140)
        card.add_widget(Label(text="Приступ идёт прямо сейчас?",
                              bold=True, font_size="14sp", color=INK,
                              size_hint_y=None, height=dp(24)))
        self.active_lbl = Label(text="Нажмите «Приступ начался».",
                                color=ACC, size_hint_y=None,
                                height=dp(28), font_size="12sp")
        card.add_widget(self.active_lbl)
        btn_row = BoxLayout(size_hint_y=None, height=dp(52),
                            spacing=dp(8))
        s = Button(text="▶ Начался", background_color=GOOD)
        s.bind(on_release=self.start_now)
        e = Button(text="■ Закончился", background_color=BAD)
        e.bind(on_release=self.stop_now)
        btn_row.add_widget(s)
        btn_row.add_widget(e)
        card.add_widget(btn_row)
        root.add_widget(card)

        help_box = BoxLayout(orientation="vertical", size_hint_y=None,
                             spacing=dp(2))
        help_box.bind(minimum_height=help_box.setter("height"))
        for line in HELP_TEXT.split("\n"):
            lab = Label(text=line or " ", color=INK, halign="left",
                        valign="middle", size_hint_y=None, height=dp(22),
                        font_size="11sp")
            lab.bind(size=lambda inst, val:
                     setattr(inst, "text_size", val))
            if line.isupper() and line.strip():
                lab.bold = True
                lab.color = BAD if line.startswith("СРОЧНО") else ACC
            help_box.add_widget(lab)
        scroll = ScrollView()
        scroll.add_widget(help_box)
        root.add_widget(scroll)

        doc_btn = Button(text="Открыть сводку для врача",
                         size_hint_y=None, height=dp(44),
                         background_color=ACC)
        doc_btn.bind(on_release=self.doctor_summary)
        root.add_widget(doc_btn)
        self.add_widget(root)

    def on_pre_enter(self, *a):
        self._show_active()
        return True

    def _show_active(self):
        a = self.db.get_active()
        if a:
            self.active_lbl.text = (f"Приступ идёт с {a['time']} "
                                    f"({fmt_ru(a['date'])})")
        else:
            self.active_lbl.text = ("Нажмите «Приступ начался», "
                                    "и время запишется точно.")

    def start_now(self, *a):
        if self.db.get_active():
            show_message("Приступ уже отмечен. Нажмите «Закончился», "
                         "когда боль пройдёт.")
            return
        n = dt.datetime.now()
        self.db.set_active(n.date().isoformat(), n.strftime("%H:%M"))
        self._show_active()

    def stop_now(self, *a):
        a = self.db.get_active()
        if not a:
            show_message("Сначала нажмите «Начался».")
            return
        self.db.set_active(None)
        self._show_active()
        sm = self.manager
        new = sm.get_screen("new")
        new.date_input.text = a["date"]
        new.time_input.text = a["time"]
        new.end_input.text = dt.datetime.now().strftime("%H:%M")
        sm.current = "new"

    def doctor_summary(self, *a):
        try:
            app = App.get_running_app()
            path = os.path.join(app.get_report_dir(),
                                "Сводка_для_врача.txt")
            st = self.db.stats()
            lines = ["=" * 50,
                     "ДНЕВНИК ГОЛОВНОЙ БОЛИ — СВОДКА ДЛЯ ВРАЧА",
                     "=" * 50, "",
                     "Дата: " + dt.datetime.now().strftime("%d.%m.%Y %H:%M"),
                     f"Всего эпизодов: {st['n']}"]
            if st["n"]:
                lines.append(f"Средняя интенсивность: {st['avg_int']:.1f}/10")
                lines.append(f"Средняя длительность: {st['avg_dur']:.0f} мин")
            lines.append("")
            lines.append("ЧАСТОТА ТРИГГЕРОВ:")
            for name, cnt, total, share in self.db.trigger_analysis():
                if cnt:
                    lines.append(f"  {name}: {cnt}/{total} ({share*100:.0f}%)")
            lines.append("")
            lines.append("ПОСЛЕДНИЕ ЭПИЗОДЫ:")
            for e in self.db.get_episodes(limit=30):
                lines.append(e["ts"].replace("T", " "))
                lines.append(f"  Тип: {e['type']}, боль: {e['intensity']}/10, "
                             f"длительность: {e['duration_min']} мин")
                if e["triggers"]:
                    lines.append(f"  Триггеры: {e['triggers']}")
                if e["medication"]:
                    lines.append(f"  Препараты: {e['medication']}")
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            show_message(f"Сводка сохранена:\n{path}")
        except Exception as e:
            show_message(f"Ошибка: {e}")


class ReportScreen(Screen):
    def __init__(self, db, **kw):
        super().__init__(**kw)
        self.db = db
        root = BoxLayout(orientation="vertical", padding=dp(10),
                         spacing=dp(10))
        hdr = BoxLayout(size_hint_y=None, height=dp(38))
        back = Button(text="← Назад", size_hint_x=None, width=dp(90))
        back.bind(on_release=lambda *a: setattr(
            self.manager, "current", "main"))
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Отчёт", bold=True, font_size="16sp",
                             color=INK))
        root.add_widget(hdr)
        self.status = Label(text="Нажмите «Сформировать сводку».",
                            color=MUTED, halign="left", valign="top",
                            size_hint_y=None, height=dp(160))
        self.status.bind(size=lambda inst, val:
                         setattr(inst, "text_size", val))
        root.add_widget(self.status)
        b = Button(text="Сформировать сводку для врача",
                   size_hint_y=None, height=dp(48), background_color=ACC)
        b.bind(on_release=self.generate)
        root.add_widget(b)
        self.add_widget(root)

    def generate(self, *a):
        # Переиспользуем логику HelpScreen
        try:
            help_scr = self.manager.get_screen("help")
            help_scr.doctor_summary()
            self.status.text = "Сводка сформирована. См. диалог."
        except Exception as e:
            self.status.text = f"Ошибка: {e}"


# ============================== APP ==============================
class HeadacheApp(App):
    title = "Голова под контролем"

    def build(self):
        self.db = Database(self._db_path())
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MainScreen(self.db, name="main"))
        sm.add_widget(NewEpisodeScreen(self.db, name="new"))
        sm.add_widget(AnalysisScreen(self.db, name="analysis"))
        sm.add_widget(DynamicScreen(self.db, name="dynamic"))
        sm.add_widget(HelpScreen(self.db, name="help"))
        sm.add_widget(ReportScreen(self.db, name="report"))
        return sm

    def _db_path(self):
        d = self.user_data_dir
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "headache.db")

    def get_report_dir(self):
        try:
            from android.storage import primary_external_storage_path  # noqa
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
            docs = os.path.join(primary_external_storage_path(), "Documents")
            if os.path.isdir(docs):
                return docs
        except ImportError:
            pass
        desktop = os.path.join(os.path.expanduser("~"), "Documents")
        if os.path.isdir(desktop):
            return desktop
        return self.user_data_dir


if __name__ == "__main__":
    HeadacheApp().run()