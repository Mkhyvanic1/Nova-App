import math
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from plyer import tts
import threading

from Brain import get_reply, analyze_message
from Memory import load_memory, save_fact
from actions import run_action, quick_check

Window.softinput_mode = "below_target"

CYAN = (0.1, 0.9, 1, 1)
DARK_BG = (0.02, 0.05, 0.08, 1)
PANEL_BG = (0.05, 0.1, 0.14, 1)
USER_BUBBLE = (0.05, 0.25, 0.3, 1)
NOVA_BUBBLE = (0.04, 0.08, 0.1, 1)

try:
    from plyer import stt
    STT_AVAILABLE = True
except Exception:
    STT_AVAILABLE = False


class ChatBubble(Label):
    def __init__(self, text, is_user, **kwargs):
        super().__init__(
            text=text,
            size_hint_y=None,
            size_hint_x=0.8,
            pos_hint={"right": 1} if is_user else {"x": 0},
            halign="left",
            valign="middle",
            color=(0.8, 1, 1, 1) if not is_user else (1, 1, 1, 1),
            padding=(dp(14), dp(10)),
            **kwargs
        )
        self.bind(texture_size=self._update_size)
        border_color = CYAN if not is_user else (0.2, 0.8, 0.9, 1)
        with self.canvas.before:
            Color(*(USER_BUBBLE if is_user else NOVA_BUBBLE))
            self.bg = RoundedRectangle(radius=[dp(4)])
            Color(*border_color)
            self.border = Line(width=1.2)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_size(self, instance, value):
        self.text_size = (self.width, None)
        self.height = value[1] + dp(20)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)


class PhotoBubble(BoxLayout):
    def __init__(self, image_path, **kwargs):
        super().__init__(
            size_hint_y=None,
            size_hint_x=0.8,
            pos_hint={"x": 0},
            height=dp(220),
            **kwargs
        )
        with self.canvas.before:
            Color(*NOVA_BUBBLE)
            self.bg = RoundedRectangle(radius=[dp(4)])
            Color(*CYAN)
            self.border = Line(width=1.2)
        self.bind(pos=self._update_bg, size=self._update_bg)

        img = Image(source=image_path, allow_stretch=True, keep_ratio=True)
        self.add_widget(img)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)


class NovaAvatar(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(120), **kwargs)
        self._pulse_event = None
        with self.canvas:
            Color(*CYAN)
            self.outer_ring = Line(circle=(0, 0, dp(35)), width=1.5)
            Color(0.1, 0.9, 1, 0.5)
            self.mid_ring = Line(circle=(0, 0, dp(25)), width=1)
            Color(*CYAN)
            self.core = Ellipse(size=(dp(30), dp(30)))
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        cx = self.center_x
        cy = self.center_y
        self.outer_ring.circle = (cx, cy, dp(35))
        self.mid_ring.circle = (cx, cy, dp(25))
        size = self.core.size[0]
        self.core.pos = (cx - size / 2, cy - size / 2)

    def start_pulse(self):
        def pulse_step(dt):
            t = Clock.get_boottime()
            scale = 1 + 0.15 * abs(math.sin(t * 4))
            size = dp(30) * scale
            self.core.size = (size, size)
            self.core.pos = (self.center_x - size / 2, self.center_y - size / 2)
        self._pulse_event = Clock.schedule_interval(pulse_step, 1 / 30)

    def stop_pulse(self):
        if self._pulse_event:
            self._pulse_event.cancel()
            self._pulse_event = None
        self.core.size = (dp(30), dp(30))
        self._update()

    def set_mood_color(self, mood):
        colors = {
            "happy": (0.6, 0.4, 1, 1),
            "curious": (0.1, 0.9, 1, 1),
            "annoyed": (1, 0.25, 0.25, 1),
            "neutral": (0.1, 0.9, 1, 1),
        }
        c = colors.get(mood, CYAN)
        self.canvas.clear()
        with self.canvas:
            Color(*c)
            self.outer_ring = Line(circle=(0, 0, dp(35)), width=1.5)
            Color(c[0], c[1], c[2], 0.5)
            self.mid_ring = Line(circle=(0, 0, dp(25)), width=1)
            Color(*c)
            self.core = Ellipse(size=(dp(30), dp(30)))
        self._update()


class NovaRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.memory = load_memory()
        self.voice_on = False

        with self.canvas.before:
            Color(*DARK_BG)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.avatar = NovaAvatar()
        self.add_widget(self.avatar)

        self.title_label = Label(
            text="N O V A",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(18),
            bold=True,
            color=CYAN
        )
        self.add_widget(self.title_label)

        self.scroll = ScrollView()
        self.chat_box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10), size_hint_y=None)
        self.chat_box.bind(minimum_height=self.chat_box.setter("height"))
        self.scroll.add_widget(self.chat_box)
        self.add_widget(self.scroll)

        input_row = BoxLayout(size_hint_y=None, height=dp(60), padding=dp(8), spacing=dp(8))

        with input_row.canvas.before:
            Color(*PANEL_BG)
            self.input_bg = Rectangle(pos=input_row.pos, size=input_row.size)
        input_row.bind(pos=self._update_input_bg, size=self._update_input_bg)
        self._input_row_ref = input_row

        self.voice_btn = Button(
            text="VOICE",
            size_hint_x=None, width=dp(75),
            background_normal="", background_color=PANEL_BG,
            color=CYAN, font_size=dp(11)
        )
        self.voice_btn.bind(on_release=self.toggle_voice)

        self.mic_btn = Button(
            text="MIC",
            size_hint_x=None, width=dp(55),
            background_normal="", background_color=PANEL_BG,
            color=CYAN, font_size=dp(11)
        )
        self.mic_btn.bind(on_release=self.start_listening)

        self.text_input = TextInput(
            hint_text="Message Nova...",
            multiline=False,
            background_normal="",
            background_active="",
            background_color=(0.04, 0.08, 0.1, 1),
            foreground_color=CYAN,
            cursor_color=CYAN,
            hint_text_color=(0.3, 0.5, 0.55, 1)
        )
        self.text_input.bind(on_text_validate=self.send_message)

        send_btn = Button(
            text="SEND",
            size_hint_x=None, width=dp(75),
            background_normal="", background_color=(0.1, 0.5, 0.55, 1),
            color=(0, 0, 0, 1), font_size=dp(11), bold=True
        )
        send_btn.bind(on_release=self.send_message)

        input_row.add_widget(self.voice_btn)
        input_row.add_widget(self.mic_btn)
        input_row.add_widget(self.text_input)
        input_row.add_widget(send_btn)
        self.add_widget(input_row)

    def _update_input_bg(self, *args):
        self.input_bg.pos = self._input_row_ref.pos
        self.input_bg.size = self._input_row_ref.size

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_avatar_mood(self, mood):
        self.avatar.set_mood_color(mood)

    def toggle_voice(self, *args):
        self.voice_on = not self.voice_on
        self.voice_btn.text = "VOICE:ON" if self.voice_on else "VOICE"

    def start_listening(self, *args):
        if not STT_AVAILABLE:
            self.add_bubble("Speech-to-text isn't available on this device.", is_user=False)
            return
        threading.Thread(target=self.listen).start()

    def listen(self):
        try:
            stt.start()
        except Exception as e:
            Clock.schedule_once(lambda dt: self.add_bubble(f"Mic error: {e}", is_user=False))

    def add_bubble(self, text, is_user):
        bubble = ChatBubble(text=text, is_user=is_user)
        self.chat_box.add_widget(bubble)
        return bubble

    def add_photo_bubble(self, image_path):
        bubble = PhotoBubble(image_path=image_path)
        self.chat_box.add_widget(bubble)
        return bubble

    def send_message(self, *args):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.text_input.text = ""
        self.add_bubble(user_text, is_user=True)

        typing_bubble = self.add_bubble("...", is_user=False)
        self.avatar.start_pulse()
        threading.Thread(target=self.get_nova_reply, args=(user_text, typing_bubble)).start()

    def get_nova_reply(self, user_text, typing_bubble):
        offline_reply = quick_check(user_text)
        if offline_reply:
            Clock.schedule_once(lambda dt: self.update_bubble(typing_bubble, offline_reply))
            return

        try:
            analysis = analyze_message(user_text)
            action = analysis.get("action", "none")

            if action == "show_photo":
                photo_path = run_action(analysis)
                Clock.schedule_once(lambda dt: self.handle_photo_result(typing_bubble, photo_path))
                return

            if action != "none":
                action_result = run_action(analysis)
                reply = action_result if action_result else "I couldn't complete that action."
            else:
                mood = analysis.get("mood", "neutral")
                reply = get_reply(user_text, self.memory, mood=mood)

                facts = analysis.get("facts", {})
                for key, value in facts.items():
                    save_fact(key, value)
                    self.memory[key] = value

                Clock.schedule_once(lambda dt: self.set_avatar_mood(mood))

        except Exception:
            reply = "I can't reach the internet right now, so I can't think properly. Check your connection and try again."

        Clock.schedule_once(lambda dt: self.update_bubble(typing_bubble, reply))

    def handle_photo_result(self, typing_bubble, photo_path):
        self.avatar.stop_pulse()
        self.chat_box.remove_widget(typing_bubble)
        if photo_path:
            self.add_photo_bubble(photo_path)
        else:
            self.add_bubble("I couldn't find any photos to show.", is_user=False)

    def update_bubble(self, bubble, reply):
        self.avatar.stop_pulse()
        bubble.text = reply
        bubble.texture_update()
        bubble.height = bubble.texture_size[1] + dp(20)
        if self.voice_on:
            threading.Thread(target=self.speak, args=(reply,)).start()

    def speak(self, text):
        try:
            tts.speak(message=text)
        except Exception as e:
            print("TTS error:", e)


class NovaApp(App):
    def build(self):
        return NovaRoot()


if __name__ == "__main__":
    NovaApp().run()
