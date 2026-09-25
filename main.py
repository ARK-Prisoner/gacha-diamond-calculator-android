# -*- coding: utf-8 -*-
import os

# 解除 Kivy 默认 60fps 上限（必须在导入 kivy 之前设置；配置项名是 maxfps）
os.environ.setdefault("KCFG_GRAPHICS_MAXFPS", "144")

import math
from datetime import date, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle, RoundedRectangle, Triangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ---------------------------------------------------------------------------
# 颜色（莫兰迪色系，与原 tkinter 版保持一致）
# ---------------------------------------------------------------------------
WHITE = "#FFFFFF"
BG = "#FBF9F6"
MORANDI_GRAY = "#B8B0A6"
MORANDI_BLUE = "#8FA3B5"
MORANDI_GREEN = "#A3B18A"
MORANDI_PINK = "#D5B8B0"
MORANDI_PURPLE = "#B0A5C0"
MORANDI_TEXT = "#5C5C5C"
MORANDI_BORDER = "#D8CFC4"
DEBUG_FPS = False


def rgb(hexstr):
    h = hexstr.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def style_input(widget):
    """把所有输入控件统一成与 TextInput 完全相同的背景贴图。"""
    atlas = "atlas://data/images/defaulttheme/textinput"
    for attr in ("background_normal", "background_down", "background_active",
                 "background_disabled_normal", "background_disabled_active"):
        if hasattr(widget, attr):
            setattr(widget, attr, atlas)
    if hasattr(widget, "background_color"):
        widget.background_color = (1, 1, 1, 1)
    if hasattr(widget, "border"):
        widget.border = [4, 4, 4, 4]


FONT = "Roboto"


def setup_font():
    """注册中文字体：优先使用打包进 fonts/ 的 Noto Sans SC，其次 Windows 系统字体。"""
    global FONT
    base = os.path.dirname(os.path.abspath(__file__))
    regular = os.path.join(base, "fonts", "NotoSansSC-Regular.otf")
    bold = os.path.join(base, "fonts", "NotoSansSC-Bold.otf")
    if os.path.exists(regular):
        try:
            LabelBase.register(name="CJK",
                               fn_regular=regular,
                               fn_bold=bold if os.path.exists(bold) else regular)
            FONT = "CJK"
            return
        except Exception:
            pass
    if os.name == "nt":
        for p in [r"C:\Windows\Fonts\msyh.ttc",
                  r"C:\Windows\Fonts\msyh.ttf",
                  r"C:\Windows\Fonts\simhei.ttf"]:
            if os.path.exists(p):
                try:
                    LabelBase.register(name="CJK", fn_regular=p)
                    FONT = "CJK"
                    return
                except Exception:
                    continue


def count_month_starts(start, end):
    count = 0
    d = start
    while d <= end:
        if d.day == 1:
            count += 1
        d += timedelta(days=1)
    return count


def enable_high_refresh_rate(target=144.0):
    """安卓端在 UI 线程向系统请求最高屏幕刷新率（默认 144Hz）；桌面端自动跳过。"""
    try:
        from android import mActivity
        from android.runnable import run_on_ui_thread
    except Exception:
        return

    @run_on_ui_thread
    def _apply():
        try:
            window = mActivity.getWindow()
            attrs = window.getAttributes()
            try:
                attrs.preferredRefreshRate = float(target)
            except Exception as exc:
                print("refresh-rate: preferredRefreshRate failed: %r" % (exc,))
            try:
                display = window.getWindowManager().getDefaultDisplay()
                current = display.getMode()
                best = None
                for mode in display.getSupportedModes():
                    same_res = (mode.getPhysicalWidth() == current.getPhysicalWidth()
                                and mode.getPhysicalHeight() == current.getPhysicalHeight())
                    if same_res and (best is None
                                     or mode.getRefreshRate() > best.getRefreshRate()):
                        best = mode
                if best is not None:
                    attrs.preferredDisplayModeId = best.getModeId()
                    print("refresh-rate: chose mode %s @ %.1fHz"
                          % (best.getModeId(), best.getRefreshRate()))
            except Exception as exc:
                print("refresh-rate: mode pick failed: %r" % (exc,))
            window.setAttributes(attrs)
            print("refresh-rate: applied (target=%.0f)" % target)
        except Exception as exc:
            print("refresh-rate: apply failed: %r" % (exc,))

    _apply()


# ---------------------------------------------------------------------------
# 下拉箭头（用 canvas 画三角形，避免字体缺字）
# ---------------------------------------------------------------------------
class ArrowDown(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas:
            Color(*rgb(MORANDI_BLUE))
            self._tri = Triangle(points=[])
        self.bind(pos=self._update, size=self._update)
        self._update()

    def _update(self, *a):
        x, y, w, h = self.x, self.y, self.width, self.height
        self._tri.points = [x, y + h, x + w, y + h, x + w / 2.0, y]


# ---------------------------------------------------------------------------
# 卡片容器（白色圆角背景 + 标题）
# ---------------------------------------------------------------------------
class Card(BoxLayout):
    def __init__(self, title, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [dp(16), dp(10), dp(16), dp(14)]
        self.spacing = dp(2)
        self.bind(minimum_height=self.setter("height"))

        with self.canvas.before:
            Color(*rgb(WHITE))
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=self._upd_bg, size=self._upd_bg)

        title_lbl = Label(text=title, color=rgb(MORANDI_BLUE) + [1],
                          font_size=sp(16), bold=True, font_name=FONT,
                          size_hint_y=None, height=dp(30),
                          halign="left", valign="middle")
        title_lbl.bind(size=lambda *a: setattr(title_lbl, "text_size", title_lbl.size))
        self.add_widget(title_lbl)

    def _upd_bg(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size


# ---------------------------------------------------------------------------
# 日期选择弹窗（纯 Kivy 自制滚轮式）
# ---------------------------------------------------------------------------
class DatePickerPopup(ModalView):
    ITEM_H = dp(40)
    SPACING = dp(2)

    def __init__(self, initial, on_select, **kw):
        super().__init__(**kw)
        self.initial = initial
        self.on_select = on_select
        self.year = initial.year
        self.month = initial.month
        self.day = initial.day
        self.size_hint = (0.94, 0.86)
        self.auto_dismiss = False
        self._cols = {}
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(10))
        root.add_widget(Label(text="选择日期", font_size=sp(18), bold=True,
                              color=rgb(MORANDI_BLUE) + [1], font_name=FONT,
                              size_hint_y=None, height=dp(40)))

        years = list(range(self.initial.year - 5, self.initial.year + 21))
        months = list(range(1, 13))
        days = list(range(1, 32))

        cols = BoxLayout(orientation="horizontal", spacing=dp(6))
        cols.add_widget(self._make_col("年", years, self.year, self._set_year))
        cols.add_widget(self._make_col("月", months, self.month, self._set_month))
        cols.add_widget(self._make_col("日", days, self.day, self._set_day))
        root.add_widget(cols)

        btns = BoxLayout(orientation="horizontal", spacing=dp(10),
                         size_hint_y=None, height=dp(50))
        cancel = Button(text="取消", font_name=FONT, font_size=sp(15),
                        color=rgb(MORANDI_TEXT) + [1],
                        background_normal="", background_down="",
                        background_color=rgb("#EDE8E0") + [1])
        cancel.bind(on_release=lambda *a: self.dismiss())
        ok = Button(text="确定", font_name=FONT, font_size=sp(15),
                    color=rgb(WHITE) + [1],
                    background_normal="", background_down="",
                    background_color=rgb(MORANDI_GREEN) + [1])
        ok.bind(on_release=self._confirm)
        btns.add_widget(cancel)
        btns.add_widget(ok)
        root.add_widget(btns)
        self.add_widget(root)

        for name, value in (("年", self.year), ("月", self.month), ("日", self.day)):
            self._highlight(name, value)
            Clock.schedule_once(lambda dt, n=name, v=value: self._scroll_to(n, v), 0.1)

    def _make_col(self, title, values, selected, on_choose):
        col = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
        col.add_widget(Label(text=title, font_size=sp(14), bold=True,
                             color=rgb(MORANDI_BLUE) + [1], font_name=FONT,
                             size_hint_y=None, height=dp(26)))
        sv = ScrollView(size_hint_y=1, do_scroll_x=False)
        grid = GridLayout(cols=1, size_hint_y=None, spacing=self.SPACING)
        grid.bind(minimum_height=grid.setter("height"))
        buttons = []
        for v in values:
            b = Button(text=str(v), size_hint_y=None, height=self.ITEM_H,
                       font_name=FONT, font_size=sp(15),
                       background_normal="", background_down="",
                       background_color=rgb("#F2EEE8") + [1],
                       color=rgb(MORANDI_TEXT) + [1])
            b.value = v
            b.bind(on_release=lambda inst, val=v: on_choose(val))
            grid.add_widget(b)
            buttons.append(b)
        sv.add_widget(grid)
        col.add_widget(sv)
        self._cols[title] = {"sv": sv, "grid": grid, "buttons": buttons}
        return col

    def _set_year(self, v):
        self.year = v
        self._highlight("年", v)

    def _set_month(self, v):
        self.month = v
        self._highlight("月", v)

    def _set_day(self, v):
        self.day = v
        self._highlight("日", v)

    def _highlight(self, name, value):
        ref = self._cols.get(name)
        if not ref:
            return
        for b in ref["buttons"]:
            if b.value == value:
                b.background_color = rgb(MORANDI_BLUE) + [1]
                b.color = rgb(WHITE) + [1]
            else:
                b.background_color = rgb("#F2EEE8") + [1]
                b.color = rgb(MORANDI_TEXT) + [1]

    def _scroll_to(self, name, value):
        ref = self._cols.get(name)
        if not ref:
            return
        sv = ref["sv"]
        grid = ref["grid"]
        buttons = ref["buttons"]
        idx = next((i for i, b in enumerate(buttons) if b.value == value), 0)
        total = grid.height
        viewport = sv.height
        if total <= viewport or total <= 0:
            sv.scroll_y = 1.0
            return
        item = self.ITEM_H + self.SPACING
        top_offset = idx * item - (viewport - self.ITEM_H) / 2
        top_offset = max(0.0, min(top_offset, total - viewport))
        sv.scroll_y = 1.0 - top_offset / (total - viewport)

    def _confirm(self, *a):
        year = self.year
        month = self.month
        day = self.day
        if month == 2:
            is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            day = min(day, 29 if is_leap else 28)
        elif month in (4, 6, 9, 11):
            day = min(day, 30)
        try:
            result = date(year, month, day)
        except ValueError:
            result = date(year, month, 1)
        self.on_select(result)
        self.dismiss()


# ---------------------------------------------------------------------------
# 主界面
# ---------------------------------------------------------------------------
class GachaCalcUI(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.inputs = {}
        self.constants = {}
        self.result_labels = {}
        self._syncing = False
        self.start_date = date.today()
        self.end_date = date.today()

        with self.canvas.before:
            Color(*rgb(BG))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_root_bg, size=self._upd_root_bg)

        self._build_header()
        self._build_body()
        self.calculate()

    def _upd_root_bg(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _build_header(self):
        self.header = BoxLayout(size_hint_y=None, height=dp(56), orientation="vertical")
        with self.header.canvas.before:
            Color(*rgb(MORANDI_BLUE))
            self.header._hbg = Rectangle(pos=self.header.pos, size=self.header.size)
        self.header.bind(pos=self._upd_hbg, size=self._upd_hbg)
        title = Label(text="攒钻 · 抽卡计算器", color=rgb(WHITE) + [1],
                      font_size=sp(20), bold=True, font_name=FONT,
                      halign="center", valign="middle")
        title.bind(size=lambda *a: setattr(title, "text_size", title.size))
        self.header.add_widget(title)
        self.add_widget(self.header)

    def _upd_hbg(self, *a):
        self.header._hbg.pos = self.header.pos
        self.header._hbg.size = self.header.size

    def _build_body(self):
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", size_hint_y=None,
                            padding=[dp(14), dp(14), dp(14), dp(20)],
                            spacing=dp(12))
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(self._build_input_card())
        content.add_widget(self._build_const_card())
        content.add_widget(self._build_result_card())

        self.info_label = Label(text="", color=rgb(MORANDI_GRAY) + [1],
                                font_size=sp(12), font_name=FONT,
                                size_hint_y=None, height=dp(30),
                                halign="center", valign="middle")
        self.info_label.bind(size=lambda *a: setattr(self.info_label, "text_size",
                                                     self.info_label.size))
        content.add_widget(self.info_label)

        note = Label(text="注意！！！攒抽计算机向下取整", color=rgb(MORANDI_PINK) + [1],
                     font_size=sp(14), bold=True, font_name=FONT,
                     size_hint_y=None, height=dp(32),
                     halign="center", valign="middle")
        note.bind(size=lambda *a: setattr(note, "text_size", note.size))
        content.add_widget(note)

        scroll.add_widget(content)
        self.add_widget(scroll)

    # ---- 输入卡片 ----
    def _build_input_card(self):
        card = Card("输入")
        self._build_date_rows(card)
        self._add_num_field(card, "多久之后（天）", "days_after", "0", self.inputs,
                            on_text=self._on_days_text)
        self._add_num_field(card, "免费抽剩多少", "free_draws", "0", self.inputs)
        self._add_spinner_field(card, "抽几辆", "how_many", "1", list(range(1, 13)), self.inputs)
        self._add_spinner_field(card, "保底多少抽", "pity", "90",
                                ["90", "100", "115", "160", "190"], self.inputs)
        self._add_num_field(card, "还剩多少钻石", "diamonds_now", "0", self.inputs)
        self._add_num_field(card, "已经抽了几发", "drawn", "0", self.inputs)
        return card

    def _build_date_rows(self, card):
        row = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(44), spacing=dp(8))
        row.add_widget(self._field_label("开始日期"))
        self.start_btn = self._date_button(self.start_date)
        self.start_btn.bind(on_release=lambda *a: self._on_start_pick())
        row.add_widget(self.start_btn)
        card.add_widget(row)

        row = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(44), spacing=dp(8))
        row.add_widget(self._field_label("最终日期"))
        self.end_btn = self._date_button(self.end_date)
        self.end_btn.bind(on_release=lambda *a: self._on_end_pick())
        row.add_widget(self.end_btn)
        card.add_widget(row)

    # ---- 常数卡片 ----
    def _build_const_card(self):
        card = Card("神秘常数")
        self._add_num_field(card, "月卡", "monthly_card", "150", self.constants)
        self._add_num_field(card, "月卡月初奖励", "monthly_bonus", "1500", self.constants)
        self._add_num_field(card, "签到", "sign_in", "20", self.constants)
        self._add_num_field(card, "每日任务", "daily_task", "270", self.constants)
        self._add_num_field(card, "每周任务", "weekly_task", "500", self.constants)
        self._add_num_field(card, "每周任务额外", "weekly_extra", "150", self.constants)
        self._add_num_field(card, "平均一周活动奖励", "weekly_event", "100", self.constants)
        return card

    # ---- 结果卡片 ----
    def _build_result_card(self):
        card = Card("结果")
        rows = [
            ("总计新增钻石", "total_new", "钻", MORANDI_PURPLE),
            ("换算抽数", "new_draws", "抽", MORANDI_PINK),
            ("到时候共有钻石", "total_diamonds", "钻", MORANDI_PURPLE),
            ("换算抽数", "total_draws", "抽", MORANDI_PINK),
        ]
        for label, key, unit, color in rows:
            self._add_result_row(card, label, key, unit, color)

        sep = BoxLayout(size_hint_y=None, height=dp(1))
        self.result_card_sep = sep
        with sep.canvas.before:
            Color(*rgb(MORANDI_BORDER))
            sep._s = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=self._upd_sep, size=self._upd_sep)
        card.add_widget(sep)

        rows2 = [
            ("一共需要钻石", "need", "钻", MORANDI_PURPLE),
            ("至少还需要", "still_need", "钻", MORANDI_PURPLE),
            ("换算抽数", "still_need_draws", "抽", MORANDI_PINK),
        ]
        for label, key, unit, color in rows2:
            self._add_result_row(card, label, key, unit, color)

        btn = Button(text="计 算", font_name=FONT, font_size=sp(16), bold=True,
                     color=rgb(WHITE) + [1],
                     background_normal="", background_down="",
                     background_color=rgb(MORANDI_GREEN) + [1],
                     size_hint_y=None, height=dp(48))
        btn.bind(on_release=lambda *a: self.calculate())
        card.add_widget(btn)
        return card

    def _upd_sep(self, *a):
        sep = self.result_card_sep
        sep._s.pos = sep.pos
        sep._s.size = sep.size

    # ---- 通用构件 ----
    def _field_label(self, text):
        lbl = Label(text=text, color=rgb(MORANDI_TEXT) + [1],
                    font_size=sp(13), font_name=FONT,
                    size_hint_x=0.44, halign="left", valign="middle")
        lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
        return lbl

    def _date_button(self, d):
        b = Button(text=d.strftime("%Y-%m-%d"), font_name=FONT, font_size=sp(14),
                   color=rgb(MORANDI_TEXT) + [1],
                   size_hint_x=0.56, size_hint_y=None, height=dp(38))
        style_input(b)
        return b

    def _add_num_field(self, card, label, key, default, store, on_text=None):
        row = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(44), spacing=dp(8))
        row.add_widget(self._field_label(label))
        ti = TextInput(text=str(default), multiline=False, input_filter="int",
                       halign="center", font_size=sp(14), font_name=FONT,
                       size_hint_x=0.56, size_hint_y=None, height=dp(38),
                       foreground_color=rgb(MORANDI_TEXT) + [1],
                       cursor_color=rgb(MORANDI_BLUE) + [1],
                       padding=[dp(8), dp(8), dp(8), dp(8)], write_tab=False)
        style_input(ti)
        if on_text:
            ti.bind(text=on_text)
        row.add_widget(ti)
        card.add_widget(row)
        store[key] = ti
        return ti

    def _add_spinner_field(self, card, label, key, default, values, store):
        row = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(44), spacing=dp(8))
        row.add_widget(self._field_label(label))
        holder = FloatLayout(size_hint_x=0.56, size_hint_y=None, height=dp(38))
        spn = Spinner(text=str(default), values=[str(v) for v in values],
                      font_name=FONT, font_size=sp(14),
                      color=rgb(MORANDI_TEXT) + [1],
                      size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        style_input(spn)
        holder.add_widget(spn)
        arrow = ArrowDown(size_hint=(None, None), size=(dp(10), dp(6)))
        arrow.pos_hint = {"right": 0.95, "center_y": 0.5}
        holder.add_widget(arrow)
        row.add_widget(holder)
        card.add_widget(row)
        store[key] = spn
        return spn

    def _add_result_row(self, card, label, key, unit, color):
        row = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(34), spacing=dp(8))
        lbl = Label(text=label, color=rgb(MORANDI_TEXT) + [1],
                    font_size=sp(13), font_name=FONT,
                    size_hint_x=0.5, halign="left", valign="middle")
        lbl.bind(size=lambda *a: setattr(lbl, "text_size", lbl.size))
        val = Label(text="—", color=rgb(color) + [1], font_size=sp(15),
                    bold=True, font_name=FONT, size_hint_x=0.3,
                    halign="right", valign="middle")
        val.bind(size=lambda *a: setattr(val, "text_size", val.size))
        unit_lbl = Label(text=unit, color=rgb(MORANDI_GRAY) + [1],
                         font_size=sp(12), font_name=FONT, size_hint_x=0.2,
                         halign="left", valign="middle")
        unit_lbl.bind(size=lambda *a: setattr(unit_lbl, "text_size", unit_lbl.size))
        row.add_widget(lbl)
        row.add_widget(val)
        row.add_widget(unit_lbl)
        card.add_widget(row)
        self.result_labels[key] = val
        return val

    # ---- 日期同步逻辑 ----
    def _on_start_pick(self):
        DatePickerPopup(self.start_date, self._set_start).open()

    def _on_end_pick(self):
        DatePickerPopup(self.end_date, self._set_end).open()

    def _set_start(self, d):
        self.start_date = d
        self.start_btn.text = d.strftime("%Y-%m-%d")
        days = self._days_value()
        self.end_date = self.start_date + timedelta(days=days)
        self.end_btn.text = self.end_date.strftime("%Y-%m-%d")

    def _set_end(self, d):
        start = self.start_date
        days = (d - start).days
        if days < 0:
            days = 0
            d = start
        self.end_date = d
        self.end_btn.text = d.strftime("%Y-%m-%d")
        self._syncing = True
        self.inputs["days_after"].text = str(days)
        self._syncing = False

    def _on_days_text(self, ti, value):
        if self._syncing:
            return
        try:
            days = int(value)
        except ValueError:
            return
        self._syncing = True
        self.end_date = self.start_date + timedelta(days=days)
        self.end_btn.text = self.end_date.strftime("%Y-%m-%d")
        self._syncing = False

    def _days_value(self):
        try:
            return int(self.inputs["days_after"].text)
        except ValueError:
            return 0

    # ---- 计算逻辑 ----
    def calculate(self):
        try:
            free_draws = int(self.inputs["free_draws"].text)
            how_many = int(self.inputs["how_many"].text)
            pity = int(self.inputs["pity"].text)
            diamonds_now = int(self.inputs["diamonds_now"].text)

            monthly_card = int(self.constants["monthly_card"].text)
            monthly_bonus = int(self.constants["monthly_bonus"].text)
            sign_in = int(self.constants["sign_in"].text)
            daily_task = int(self.constants["daily_task"].text)
            weekly_task = int(self.constants["weekly_task"].text)
            weekly_extra = int(self.constants["weekly_extra"].text)
            weekly_event = int(self.constants["weekly_event"].text)
        except ValueError:
            self.info_label.text = "输入无效，请填写整数"
            self.info_label.color = rgb(MORANDI_PINK) + [1]
            return

        start = self.start_date
        end = self.end_date
        days_after = (end - start).days
        if days_after < 0:
            days_after = 0
        weeks = math.ceil(days_after / 7)
        weeks_ratio = (days_after + 1) / 7
        month_starts = count_month_starts(start, end)

        total_new = (
            (monthly_card + sign_in + daily_task) * days_after
            + (weekly_task + weekly_extra) * weeks
            + math.floor(weekly_event * weeks_ratio)
            + month_starts * monthly_bonus
        )
        new_draws = math.floor(total_new / 150)

        total_diamonds = total_new + diamonds_now
        total_draws = math.floor(total_diamonds / 150)

        need = how_many * pity * 150
        still_need = max(need - total_diamonds - free_draws * 150, 0)
        still_need_draws = still_need // 150

        self.result_labels["total_new"].text = str(total_new)
        self.result_labels["new_draws"].text = str(new_draws)
        self.result_labels["total_diamonds"].text = str(total_diamonds)
        self.result_labels["total_draws"].text = str(total_draws)
        self.result_labels["need"].text = str(need)
        self.result_labels["still_need"].text = str(still_need)
        self.result_labels["still_need_draws"].text = str(still_need_draws)

        self.info_label.text = (
            f"{start} → {end}（{days_after} 天后）· 周数 {weeks} · 月初 {month_starts} 次"
        )
        self.info_label.color = rgb(MORANDI_GRAY) + [1]


class GachaCalcApp(App):
    def build(self):
        setup_font()
        return GachaCalcUI()

    def on_start(self):
        enable_high_refresh_rate()
        if DEBUG_FPS:
            Clock.schedule_interval(self._log_fps, 2.0)

    def _log_fps(self, dt):
        print("FPS = %.1f" % Clock.get_fps())


if __name__ == "__main__":
    GachaCalcApp().run()
