from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.lang.builder import Builder
from kivy.uix.label import Label
from kivy.properties import NumericProperty, BooleanProperty
from kivy.core.window import Window
from kivy.clock import Clock
import math
# from kivy.core.audio import SoundLoader
import random

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

MOVE_SPEED = 10
BULLET_SPEED = 30
ENEMY_SPEED = 4


Builder.load_string('''
<RotatedImage>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: root.rotate_angle
            axis: 0, 0, 1
            origin: root.center
    canvas.after:
        PopMatrix
''')


class RotatedImage(Image):
    rotate_angle = NumericProperty(0)


class Bullet(Image):
    def __init__(self, screen_size, angle):
        super().__init__()
        self.source = 'bullet.png'
        self.size = (10, 10)
        self.size_hint = (None, None)
        w, h = screen_size
        self.pos = (w / 2, h / 2)

        self.angle = angle

        # self.sound = SoundLoader.load('splat.wav')
        # self.sound.play()


class Player(RotatedImage):
    shooting = BooleanProperty(False)

    def __init__(self):
        super().__init__()
        self.source = 'player.png'
        self.size = (100, 100)
        self.hp = 50
        self.size_hint = (None, None)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, window, pos):
        cur_x = self.x + 50
        cur_y = self.y + 50
        mouse_x = pos[0] - cur_x
        mouse_y = pos[1] - cur_y

        angle = math.degrees(math.atan2(mouse_x, mouse_y)) % 360
        self.angle = angle
        self.rotate_angle = 360 - angle

    def on_touch_down(self, touch):
        self.shooting = True

    def on_touch_up(self, touch):
        self.shooting = False


class TunaCan(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.health = 3
        self.source = 'tunacan.png'
        self.angle = 0

    def recalc_angle(self, screen):
        cur_x = self.x + 50
        cur_y = self.y + 50
        player_x = (screen.width / 2) - cur_x
        player_y = (screen.height / 2) - cur_y

        angle = math.degrees(math.atan2(player_x, player_y)) % 360
        self.angle = angle


class Nori(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.health = 10
        self.source = 'deepseanori.png'
        self.angle = 0

    def recalc_angle(self, screen):
        cur_x = self.x + 50
        cur_y = self.y + 50
        player_x = (screen.width / 2) - cur_x
        player_y = (screen.height / 2) - cur_y

        angle = math.degrees(math.atan2(player_x, player_y)) % 360
        self.angle = angle


class WaveGenerator():
    def __init__(self, screen):
        self.wave = 0
        self.screen = screen
        self.script = [
            {'tunas': 15, 'time': 30},
            {'tunas': 10, 'nori': 3, 'time': 4}
        ]
        Clock.schedule_once(self.next_wave, 0.5)

    def next_wave(self, dt):
        print("Next wave!!")
        if self.wave >= len(self.script):
            return
        wave_script = self.script[self.wave]
        time = wave_script['time']
        tunas = wave_script.get('tunas', 0)
        noris = wave_script.get('nori', 0)

        for i in range(0, tunas):
            spawn_time = ((time * 0.8) / tunas) * i
            Clock.schedule_once(self.spawn_tuna, spawn_time)
        self.spawn_tuna(0)

        for i in range(0, noris):
            spawn_time = ((time * 0.8) / noris) * i
            Clock.schedule_once(self.spawn_nori, spawn_time)

        self.wave += 1
        Clock.schedule_once(self.next_wave, time)

    def get_spawn_point(self):
        w, h = self.screen.size

        left_x_range = (-100, 0)
        right_x_range = (w, w + 100)
        lr_y_range = (-100, h + 100)

        tb_x_range = (0, w)
        top_y_range = (h, h + 100)
        bottom_y_range = (-100, 0)

        lr_x_opt_1 = random.randint(*left_x_range)
        lr_x_opt_2 = random.randint(*right_x_range)
        lr_x = random.choice([lr_x_opt_1, lr_x_opt_2])
        lr_y = random.randint(*lr_y_range)

        tb_y_opt_1 = random.randint(*top_y_range)
        tb_y_opt_2 = random.randint(*bottom_y_range)
        tb_y = random.choice([tb_y_opt_1, tb_y_opt_2])
        tb_x = random.randint(*tb_x_range)

        return random.choice([(lr_x, lr_y), (tb_x, tb_y)])

    def spawn_tuna(self, dt):
        pos = self.get_spawn_point()
        tuna = TunaCan(size_hint=(None, None), pos=pos)
        self.screen.add_widget(tuna, 1)
        self.screen.enemies.append(tuna)

    def spawn_nori(self, dt):
        pos = self.get_spawn_point()
        nori = Nori(size_hint=(None, None), pos=pos)
        self.screen.add_widget(nori, 1)
        self.screen.enemies.append(nori)


class GameScreen(Screen):
    def __init__(self):
        super().__init__()
        self.bullets = []
        self.enemies = []
        self.wave_gen = WaveGenerator(self)

        bg_img = Image(source='sea.png', keep_ratio=False, allow_stretch=True)
        self.add_widget(bg_img)

        self.map_img = Image(source='map.jpg', width=2445, height=2156,
                             size_hint=(None, None), pos=(-800, -800))
        self.add_widget(self.map_img)

        self.player = Player()
        self.add_widget(self.player)
        self.player.bind(shooting=self.shoot)

        self._keyboard = Window.request_keyboard(
            self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self.key_down)
        self._keyboard.bind(on_key_up=self.key_up)

        self.old_size = None

        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False

        Clock.schedule_interval(self.update, 1 / 30)

    def on_size(self, e, size):
        w, h = size
        if self.old_size:
            ow, oh = self.old_size

            xdiff = (w - ow) / 2
            ydiff = (h - oh) / 2
            self.map_img.x += xdiff
            self.map_img.y += ydiff

            for e in self.enemies:
                e.x += xdiff
                e.y += ydiff

        self.old_size = w, h

    def shoot(self, e, shooting):
        if shooting:
            b = Bullet(self.size, e.angle)
            self.bullets.append(b)
            self.add_widget(b, 1)

    def key_down(self, keyboard, key, text, mod):
        if text == 'w':
            self.move_up = True
        elif text == 'a':
            self.move_left = True
        elif text == 's':
            self.move_down = True
        elif text == 'd':
            self.move_right = True

    def key_up(self, keyboard, key):
        key = key[1]
        if key == 'w':
            self.move_up = False
        elif key == 'a':
            self.move_left = False
        elif key == 's':
            self.move_down = False
        elif key == 'd':
            self.move_right = False

    def _keyboard_closed(self, **kwargs):
        pass

    def update(self, e):
        x_move = 0
        y_move = 0
        if self.move_up:
            y_move -= MOVE_SPEED
        if self.move_down:
            y_move += MOVE_SPEED
        if self.move_left:
            x_move += MOVE_SPEED
        if self.move_right:
            x_move -= MOVE_SPEED
        if self.player.hp <= 0:
            x_move = y_move = 0

        self.map_img.x += x_move
        self.map_img.y += y_move
        if not self.enemies and self.wave_gen.wave >= len(self.wave_gen.script):
            label = Label(text="WINNER", font_size=32)
            self.add_widget(label)

        for e in self.enemies:
            e.x += x_move
            e.y += y_move
            if self.player.hp > 0:
                e.recalc_angle(self)

            C = math.radians(90)
            B = math.radians(e.angle)
            A = math.radians(180) - C - B
            c = ENEMY_SPEED
            a = (c / math.sin(C)) * math.sin(A)
            b = (c / math.sin(C)) * math.sin(B)

            e.x += b
            e.y += a

            if e.collide_point(self.width / 2, self.height / 2):
                self.player.hp -= 1
                if self.player.hp <= 0:
                    label = Label(text="WASTED", font_size=32)
                    self.add_widget(label)

        used_bullets = []
        for bullet in self.bullets:
            C = math.radians(90)
            B = math.radians(bullet.angle)
            A = math.radians(180) - C - B
            c = BULLET_SPEED
            a = (c / math.sin(C)) * math.sin(A)
            b = (c / math.sin(C)) * math.sin(B)

            bullet.x += b
            bullet.y += a

            killed_enemies = []
            for e in self.enemies:
                if e.collide_point(*bullet.pos):
                    e.health -= 1
                    if e.health <= 0:
                        self.remove_widget(e)
                        killed_enemies.append(e)
                    self.remove_widget(bullet)
                    used_bullets.append(bullet)
                    break
            for e in killed_enemies:
                self.enemies.remove(e)
        for b in used_bullets:
            self.bullets.remove(b)


class InkfantryApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(GameScreen())
        return sm


if __name__ == '__main__':
    InkfantryApp().run()
