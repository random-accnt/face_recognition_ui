import os
import threading
import time
from os.path import dirname

import face_recognition
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from app.file_chooser import FolderSelectDialog, LoadDialog

# load files
Builder.load_file("app/file_chooser.kv")


class InfoRow(BoxLayout):
    key = StringProperty("")
    value = StringProperty("")
    font_size = NumericProperty(20)

    def on_size(self, instance, value):
        self.set_height()

    def on_value(self, instance, value):
        thread = threading.Thread(target=self.delayed_update)
        thread.start()

    def set_height(self):
        self.height = max([self.ids.label_key.height, self.ids.label_value.height])

    def delayed_update(self):
        # for now just wait 0.3 s, find beter way later
        time.sleep(0.3)
        self.set_height()


class RowGroup(BoxLayout):
    data = ListProperty()

    def __init__(self, **kwargs):
        super(RowGroup, self).__init__(**kwargs)
        self.setup_rows()

    def setup_rows(self):
        for i, (name, dist) in enumerate(self.data):
            row = InfoRow(key=f"{i+2})", value=name, font_size=15)
            self.add_widget(row)

    def on_data(self, instance, value):
        self.setup_rows()


class SelectedImage(BoxLayout):
    filepath = StringProperty("")
    custom_label = Label(text="Drag and drop image or click to select", font_size=20)

    def __init__(self, **kwargs):
        super(SelectedImage, self).__init__(**kwargs)
        self.do_the_stuff(self.filepath)

    def on_filepath(self, instance, value):
        self.do_the_stuff(value)

    def do_the_stuff(self, value):
        if value:
            self.show_image()
        else:
            self.show_label()

    def show_image(self):
        self.clear_widgets()
        self.add_widget(Image(source=self.filepath))

    def show_label(self):
        self.clear_widgets()
        self.add_widget(self.custom_label)


class RecognitionWidget(Widget):
    load_file = ObjectProperty(None)
    curdir = dirname(__file__)
    image_path = StringProperty("")
    name_distance = ListProperty()
    top_name_dist = StringProperty("")
    known_faces_folder = StringProperty("")

    def close_popup(self):
        self._popup.dismiss()

    # load
    def load_show_if_empty(self):
        if self.image_path == "":
            self.load_show()

    def load_show(self):
        content = LoadDialog(load=self.load, cancel=self.close_popup)
        self._popup = Popup(title="Load image", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        try:
            selected_file = filename[0]
        except IndexError:
            print("Nothing selected")
            return

        print("Selected image: ", path + selected_file)
        self.close_popup()

        # set and reload image
        self.set_image_filepath(os.path.join(path, selected_file))

    def set_image_filepath(self, path):
        self.image_path = path
        img_widget = self.ids.selected_image_box
        img_widget.filename = self.image_path

    # select folder

    def folder_select_show(self):
        content = FolderSelectDialog(select=self.select_folder, cancel=self.close_popup)
        self._popup = Popup(
            title="Select folder with known faces",
            content=content,
            size_hint=(0.9, 0.9),
        )
        self._popup.open()

    def select_folder(self, path):
        self.known_faces_folder = path
        print(f"Selected path: {self.known_faces_folder}")
        self.close_popup()

    def evaluate(self):
        if self.image_path == "":
            print("No image selected")
            return

        print("Started evaluation")
        self.name_distance = recognize_face(self.known_faces_folder, self.image_path)
        for nd in self.name_distance:
            print(nd)

        self.top_name_dist = f"{self.name_distance[0][0]} ({self.name_distance[0][1]})"

    def on_drop_file(self, filename, x, y, *args):
        print("Dropped")


class RecognitionApp(App):
    def build(self):
        self.root = RecognitionWidget()

        if Window:
            Window.bind(on_drop_file=self.on_drop_file)

        return self.root

    def on_drop_file(self, *args):
        print(f"File dropped:\n - {args}")
        filepath = args[1].decode("utf-8")
        x = args[2]
        y = args[3]

        image = self.root.ids.selected_image_box
        if self.is_inside_widget(image, x, y):
            print("Dropped in image")
            self.root.image_path = filepath
        else:
            print("Not in any specified widget")

    def on_dropfile(self, filename):
        print("Was here")
        self.on_drop_file(filename)

    def is_inside_widget(self, widget, x, y) -> bool:
        inside_x = x >= widget.pos[0] and x <= (widget.pos[0] + widget.width)
        inside_y = y >= widget.pos[1] and y <= (widget.pos[1] + widget.height)

        return inside_x and inside_y


def recognize_face(known_faces_folder: str, unknow_image_path: str):
    known_faces_encodings = []
    names = []

    if not os.path.exists(known_faces_folder) or not os.path.isdir(known_faces_folder):
        print("Invalid know faces dir")
        return "Error"

    for filename in os.listdir(known_faces_folder):
        1
        filepath = os.path.join(known_faces_folder, filename)
        if not os.path.isfile(filepath):
            continue

        image = face_recognition.load_image_file(filepath)
        # returns list of all faces
        face_encodings = face_recognition.face_encodings(image)
        for face_encoding in face_encodings:
            known_faces_encodings.append(face_encoding)
            names.append(filename[: filename.find(".")])

    if not os.path.isfile(unknow_image_path):
        print("Invalid path to unknown face image: ", unknow_image_path)
        return "Error"

    image = face_recognition.load_image_file(unknow_image_path)
    unknown_encoding = face_recognition.face_encodings(image)[0]

    distances = face_recognition.face_distance(known_faces_encodings, unknown_encoding)
    distances = [round(x, ndigits=3) for x in distances]
    result = [x for x in zip(names, distances)]
    result.sort(key=lambda x: x[1])

    return result
