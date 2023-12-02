import os

from kivy.properties import ObjectProperty
from kivy.uix.floatlayout import FloatLayout


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    curdir = os.getcwd()


class FolderSelectDialog(FloatLayout):
    select = ObjectProperty(None)
    cancel = ObjectProperty(None)
    curdir = os.getcwd()
