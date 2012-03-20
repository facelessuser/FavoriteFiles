'''
Favorite Files
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
'''

import sublime
import sublime_plugin
from os.path import join, exists, normpath, basename, getmtime
import json
import sys

# Pull in included modules
lib = join(sublime.packages_path(), 'FavoriteFiles')
if not lib in sys.path:
    sys.path.append(lib)
from lib.file_strip.json import sanitize_json

FILES = join(sublime.packages_path(), 'User', 'favorite_files.json')


class FileList:
    files = {}
    last_access = 0

    @classmethod
    def get(cls, s):
        if cls.exists(s):
            return normpath(cls.files[s])
        else:
            return None

    @classmethod
    def set(cls, s, path):
        cls.files[s] = path

    @classmethod
    def exists(cls, s):
        return True if s in cls.files else False

    @classmethod
    def remove(cls, s):
        if cls.exists(s):
            del cls.files[s]

    @classmethod
    def keys(cls):
        return [x for x in cls.files]


def create_favorite_list(l, force=False):
    errors = False
    if not exists(FILES) or force:
        try:
            j = json.dumps(l, sort_keys=True, indent=4, separators=(',', ': '))
            with open(FILES, 'w') as f:
                f.write(j + "\n")
            FileList.last_access = getmtime(FILES)
        except:
            sublime.error_message('Failed to create favorite_files.json!')
            errors = True
    return errors


def load_favorite_files(force=False):
    errors = False
    if not exists(FILES):
        if create_favorite_list({}, True):
            errors = True
    if not errors and (force or getmtime(FILES) != FileList.last_access):
        try:
            with open(FILES, "r") as f:
                # Allow C style comments and be forgiving of trailing commas
                content = sanitize_json(f.read(), True)
            file_list = json.loads(content)
            FileList.last_access = getmtime(FILES)
            FileList.files = file_list
        except:
            errors = True
            sublime.error_message('Failed to read favorite_files.json!')
    return errors


class SelectFavoriteFileCommand(sublime_plugin.WindowCommand):
    def open_file(self, value):
        if value >= 0:
            f = FileList.get(self.files[value])
            if f != None:
                self.window.open_file(f)

    def run(self):
        if not load_favorite_files():
            self.files = FileList.keys()
            if len(self.files):
                self.window.show_quick_panel(
                    self.files,
                    self.open_file
                )
            else:
                sublime.error_message("No favorites found! Try adding some.")


class AddFavoriteFileCommand(sublime_plugin.WindowCommand):
    def add(self, value):
        if not FileList.exists(value):
            FileList.set(value, self.name)
            create_favorite_list(FileList.files, True)
        else:
            sublime.error_message("The name \"%s\" already exists!" % value)
            self.repeat_prompt()

    def repeat_prompt(self):
        view = self.window.active_view()
        if view != None:
            self.window.show_input_panel(
                "Add Favorite: ",
                self.temp_name,
                self.add,
                None,
                None
            )

    def prompt(self):
        view = self.window.active_view()
        if view != None:
            self.name = view.file_name()
            if self.name != None:
                temp_name = basename(self.name)
                idx = 0
                key = temp_name
                while FileList.exists(key):
                    key = temp_name + ("_%d" % idx)
                    idx += 1
                self.temp_name = key
                self.window.show_input_panel(
                    "Add Favorite: ",
                    key,
                    self.add,
                    None,
                    None
                )

    def run(self):
        self.prompt()


class RemoveFavoriteFileCommand(sublime_plugin.WindowCommand):
    def remove(self, value):
        if value >= 0:
            key = self.files[value]
            if FileList.exists(key):
                FileList.remove(key)
                create_favorite_list(FileList.files, True)

    def run(self):
        if not load_favorite_files():
            self.files = FileList.keys()
            if len(self.files):
                self.window.show_quick_panel(
                    self.files,
                    self.remove
                )
            else:
                sublime.error_message("No favorites found!")


load_favorite_files(True)
