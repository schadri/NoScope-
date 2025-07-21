import sys
import time
from multiprocessing import Process, Value, Manager
from ctypes import c_int
import os


def crosshair(scale_percent, resolution, shared):
    from PyQt5.QtWidgets import QApplication, QLabel
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QGuiApplication

    class FloatingImage(QLabel):
        def __init__(self, image_path, scale_percent=100, opacity=1.0):
            super().__init__()
            self.image_path = image_path
            self.scale_percent = scale_percent
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool |
                Qt.WindowTransparentForInput
            )
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setStyleSheet("background: transparent;")
            self.update_pixmap()
            self.center_on_screen()
            self.setWindowOpacity(opacity)

        def update_pixmap(self):
            pixmap = QPixmap(self.image_path)
            width = int(pixmap.width() * self.scale_percent / 100)
            height = int(pixmap.height() * self.scale_percent / 100)
            pixmap = pixmap.scaled(
                width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(pixmap)
            self.adjustSize()

        def center_on_screen(self, custom_res=None, offset_x=0, offset_y=0):
            if custom_res:
                screen_width, screen_height = custom_res
            else:
                screen = QGuiApplication.primaryScreen()
                screen_geometry = screen.geometry()
                screen_width = screen_geometry.width()
                screen_height = screen_geometry.height()
            image_width = self.width()
            image_height = self.height()
            self.move(
                int(screen_width // 2 - image_width // 2 + offset_x),
                int(screen_height // 2 - image_height // 2 + offset_y)
            )

    app = QApplication(sys.argv)
    image_path = shared.image_path if shared.image_path else "Red-Dot-White-450.png"
    opacity = getattr(shared, 'opacity', 1.0)
    viewer = FloatingImage(image_path, scale_percent.value, opacity)
    viewer.show()

    last_scale = scale_percent.value
    last_res = (resolution[0], resolution[1])
    last_img = shared.image_path
    last_offset_x = getattr(shared, 'offset_x', 0)
    last_offset_y = getattr(shared, 'offset_y', 0)
    last_opacity = opacity

    while True:
        app.processEvents()
        offset_x = getattr(shared, 'offset_x', 0)
        offset_y = getattr(shared, 'offset_y', 0)
        opacity = getattr(shared, 'opacity', 1.0)

        if scale_percent.value != last_scale:
            viewer.scale_percent = scale_percent.value
            viewer.update_pixmap()
            viewer.center_on_screen(custom_res=(
                resolution[0], resolution[1]), offset_x=offset_x, offset_y=offset_y)
            last_scale = scale_percent.value

        if (resolution[0], resolution[1]) != last_res:
            viewer.center_on_screen(custom_res=(
                resolution[0], resolution[1]), offset_x=offset_x, offset_y=offset_y)
            last_res = (resolution[0], resolution[1])

        if shared.image_path != last_img and shared.image_path:
            viewer.image_path = shared.image_path
            viewer.update_pixmap()
            viewer.center_on_screen(custom_res=(
                resolution[0], resolution[1]), offset_x=offset_x, offset_y=offset_y)
            last_img = shared.image_path

        if offset_x != last_offset_x or offset_y != last_offset_y:
            viewer.center_on_screen(custom_res=(
                resolution[0], resolution[1]), offset_x=offset_x, offset_y=offset_y)
            last_offset_x = offset_x
            last_offset_y = offset_y

        if opacity != last_opacity:
            viewer.setWindowOpacity(opacity)
            last_opacity = opacity

        time.sleep(0.05)


if __name__ == '__main__':
    from kivy.config import Config
    Config.set('graphics', 'width', '600')
    Config.set('graphics', 'height', '600')
    Config.set('graphics', 'resizable', '1')
    from multiprocessing import freeze_support, Array
    freeze_support()

    scale_percent_shared = Value(c_int, 35)
    resolution_shared = Array('i', [1920, 1080])
    manager = Manager()
    shared = manager.Namespace()
    shared.image_path = os.path.join(os.path.dirname(
        __file__), "crosshair", "Red-Dot-White-450.png")
    shared.offset_x = 0
    shared.offset_y = 0

    from kivy.uix.textinput import TextInput
    from kivy.uix.popup import Popup
    from kivy.uix.filechooser import FileChooserIconView
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.button import Button
    from kivy.uix.anchorlayout import AnchorLayout
    from kivy.properties import NumericProperty
    from kivy.uix.label import Label
    from kivy.uix.slider import Slider
    from kivy.uix.boxlayout import BoxLayout
    from kivy.app import App

    class ImageScaler(FloatLayout):
        scale_percent = NumericProperty(35)
        resolutions = [
            (640, 480), (800, 600), (1024, 768), (1280, 720), (1280, 800),
            (1366, 768), (1440, 900), (1440, 1080), (1600, 900),
            (1680, 1050), (1920, 1080), (1920, 1200), (2560, 1440), (2560, 1600)
        ]

        def __init__(self, scale_percent_shared, resolution_shared, shared, **kwargs):
            super().__init__(**kwargs)
            self.scale_percent_shared = scale_percent_shared
            self.resolution_shared = resolution_shared
            self.shared = shared
            self.res_buttons_visible = False

            from kivy.graphics import Color, Rectangle
            with self.canvas.before:
                Color(0.13, 0.15, 0.18, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self._update_bg, size=self._update_bg)

            btn_style = {
                'background_normal': '',
                'background_color': (0.22, 0.25, 0.29, 1),
                'color': (1, 1, 1, 1),
                'font_size': 16,
                'bold': True,
                'background_down': '',
            }
            slider_style = {
                'background_width': 24,
                'cursor_size': (32, 32),
                'cursor_image': '',
            }

            self.top_btn_box = BoxLayout(orientation='horizontal', size_hint=(
                None, None), size=(300, 40), pos_hint={'center_x': 0.5, 'top': 1}, spacing=10)
            self.res_btn = Button(text='Resoluciones ▼', size_hint=(
                None, None), size=(140, 35), **btn_style)
            self.res_btn.bind(on_release=self.toggle_res_buttons)
            self.img_btn = Button(text='Cambiar Crosshair', size_hint=(
                None, None), size=(140, 35), **btn_style)
            self.img_btn.bind(on_release=self.open_file_chooser)
            self.top_btn_box.add_widget(self.res_btn)
            self.top_btn_box.add_widget(self.img_btn)
            self.add_widget(self.top_btn_box)

            self.res_box = BoxLayout(
                orientation='vertical', size_hint=(None, None), width=140)
            self.res_box.height = len(self.resolutions) * 32
            self.res_box.opacity = 0
            self.res_box.disabled = True
            self.res_box.x = 0
            self.res_box.y = 0
            for w, h in self.resolutions:
                btn = Button(text=f"{w}x{h}", size_hint=(
                    1, None), height=30, **btn_style)
                btn.bind(on_release=lambda inst, w=w,
                         h=h: self.set_resolution(w, h))
                self.res_box.add_widget(btn)

            self.sliders_box = BoxLayout(orientation='horizontal', size_hint=(
                None, None), width=560, height=300, pos_hint={'x': 0, 'y': 0.2})

            # Escala
            scale_box = BoxLayout(orientation='vertical',
                                  size_hint=(None, 1), width=140)
            self.label = Label(text=f"Escala: {int(self.scale_percent)}%", size_hint=(
                1, None), height=40, halign='center', valign='middle', color=(1, 1, 1, 1), font_size=16)
            self.label.bind(size=lambda instance, value: setattr(
                instance, 'text_size', value))
            self.slider = Slider(min=10, max=100, value=self.scale_percent,
                                 step=1, orientation='vertical', size_hint=(1, 1), **slider_style)
            self.slider.bind(value=self.on_slider_value)
            scale_box.add_widget(self.label)
            scale_box.add_widget(self.slider)
            self.sliders_box.add_widget(scale_box)

            # Slider de opacidad
            self.opacity_box = BoxLayout(
                orientation='vertical', size_hint=(None, 1), width=140)
            self.label_opacity = Label(text=f"Opacidad: {int(getattr(self.shared, 'opacity', 1.0)*100)}%", size_hint=(
                1, None), height=40, halign='center', valign='middle', color=(1, 1, 1, 1), font_size=16)
            self.label_opacity.bind(
                size=lambda instance, value: setattr(instance, 'text_size', value))
            self.slider_opacity = Slider(min=10, max=100, value=getattr(
                self.shared, 'opacity', 1.0)*100, step=1, orientation='vertical', size_hint=(1, 1), **slider_style)
            self.slider_opacity.bind(value=self.on_slider_opacity_value)
            self.opacity_box.add_widget(self.label_opacity)
            self.opacity_box.add_widget(self.slider_opacity)
            self.sliders_box.add_widget(self.opacity_box)

            # Offset X
            offset_x_box = BoxLayout(
                orientation='vertical', size_hint=(None, 1), width=140)
            self.label_x = Label(text=f"X: {int(self.shared.offset_x)}", size_hint=(
                1, None), height=40, halign='center', valign='middle', color=(1, 1, 1, 1), font_size=16)
            self.label_x.bind(size=lambda instance, value: setattr(
                instance, 'text_size', value))
            self.slider_x = Slider(min=-500, max=500, value=self.shared.offset_x,
                                   step=1, orientation='vertical', size_hint=(1, 1), **slider_style)
            self.slider_x.bind(value=self.on_slider_x_value)
            offset_x_box.add_widget(self.label_x)
            offset_x_box.add_widget(self.slider_x)
            self.sliders_box.add_widget(offset_x_box)

            # Offset Y
            offset_y_box = BoxLayout(
                orientation='vertical', size_hint=(None, 1), width=140)
            self.label_y = Label(text=f"Y: {int(self.shared.offset_y)}", size_hint=(
                1, None), height=40, halign='center', valign='middle', color=(1, 1, 1, 1), font_size=16)
            self.label_y.bind(size=lambda instance, value: setattr(
                instance, 'text_size', value))
            self.slider_y = Slider(min=-500, max=500, value=self.shared.offset_y,
                                   step=1, orientation='vertical', size_hint=(1, 1), **slider_style)
            self.slider_y.bind(value=self.on_slider_y_value)
            offset_y_box.add_widget(self.label_y)
            offset_y_box.add_widget(self.slider_y)
            self.sliders_box.add_widget(offset_y_box)

            self.add_widget(self.sliders_box)

        def on_slider_opacity_value(self, instance, value):
            self.shared.opacity = float(value) / 100.0
            self.label_opacity.text = f"Opacidad: {int(value)}%"

        def _update_bg(self, *args):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

        def on_slider_value(self, instance, value):
            self.scale_percent = int(value)
            self.label.text = f"Escala: {self.scale_percent}%"
            self.scale_percent_shared.value = self.scale_percent

        def on_slider_x_value(self, instance, value):
            self.shared.offset_x = int(value)
            self.label_x.text = f"X: {self.shared.offset_x}"

        def on_slider_y_value(self, instance, value):
            self.shared.offset_y = int(value)
            self.label_y.text = f"Y: {self.shared.offset_y}"

        def open_file_chooser(self, instance):
            content = BoxLayout(orientation='vertical')
            filechooser = FileChooserIconView(
                filters=['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif'])
            filechooser.path = 'crosshair'
            btns = BoxLayout(size_hint_y=None, height=40)
            ok_btn = Button(text='Seleccionar')
            cancel_btn = Button(text='Cancelar')
            btns.add_widget(ok_btn)
            btns.add_widget(cancel_btn)
            content.add_widget(filechooser)
            content.add_widget(btns)
            popup = Popup(title='Selecciona una imagen',
                          content=content, size_hint=(0.8, 0.8))

            def select_image(instance):
                if filechooser.selection:
                    self.shared.image_path = filechooser.selection[0]
                popup.dismiss()

            def cancel(instance):
                popup.dismiss()

            ok_btn.bind(on_release=select_image)
            cancel_btn.bind(on_release=cancel)
            popup.open()

        def toggle_res_buttons(self, instance):
            self.res_buttons_visible = not self.res_buttons_visible
            if self.res_buttons_visible:
                self.show_res_box()
            else:
                self.hide_res_box()

        def show_res_box(self):
            if self.res_box.parent:
                self.remove_widget(self.res_box)
            self.do_layout()
            wx, wy = self.res_btn.to_window(self.res_btn.x, self.res_btn.y)
            root_wx, root_wy = self.to_window(self.x, self.y)
            rel_x = wx - root_wx
            rel_y = wy - root_wy
            self.res_box.x = rel_x
            self.res_box.y = rel_y - self.res_box.height
            self.add_widget(self.res_box)
            self.res_box.opacity = 1
            self.res_box.disabled = False
            self.res_btn.text = 'Resoluciones ▲'

        def hide_res_box(self):
            self.res_box.opacity = 0
            self.res_box.disabled = True
            self.res_btn.text = 'Resoluciones ▼'
            if self.res_box.parent:
                self.remove_widget(self.res_box)

        def set_resolution(self, w, h):
            self.resolution_shared[0] = w
            self.resolution_shared[1] = h
            self.shared.offset_x = 0
            self.shared.offset_y = 0
            self.slider_x.value = 0
            self.slider_y.value = 0
            self.label_x.text = "X: 0"
            self.label_y.text = "Y: 0"
            self.hide_res_box()

    class MiApp(App):
        def __init__(self, scale_percent_shared, resolution_shared, shared, **kwargs):
            super().__init__(**kwargs)
            self.scale_percent_shared = scale_percent_shared
            self.resolution_shared = resolution_shared
            self.shared = shared

        def build(self):
            return ImageScaler(self.scale_percent_shared, self.resolution_shared, self.shared)

    p = Process(target=crosshair, args=(
        scale_percent_shared, resolution_shared, shared))
    p.start()
    MiApp(scale_percent_shared, resolution_shared, shared).run()
    p.terminate()
