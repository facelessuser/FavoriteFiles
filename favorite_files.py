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

FILES = join(sublime.packages_path(), 'User', 'favorite_files_list.json')


class FileList:
    files = {}
    last_access = 0

    @classmethod
    def get(cls, s):
        if cls.exists(s):
            return normpath(cls.files["files"][s])
        else:
            return None

    @classmethod
    def remove_group(cls, s):
        if cls.exists(s, group=True):
            del cls.files["groups"][s]

    @classmethod
    def add_group(cls, s):
        cls.files["groups"][s] = {}

    @classmethod
    def set(cls, s, path, group_name=None):
        if group_name == None:
            cls.files["files"][s] = path
        else:
            cls.files["groups"][group_name][s] = path

    @classmethod
    def exists(cls, s, group=False, group_name=None):
        if group:
            return True if s in cls.files["groups"] else False
        else:
            if group_name == None:
                return True if s in cls.files["files"] else False
            else:
                return True if s in cls.files["groups"][group_name] else False

    @classmethod
    def remove(cls, s, group_name=None):
        if group_name == None:
            if cls.exists(s):
                del cls.files["files"][s]
        else:
            if cls.exists(s, group_name=group_name):
                del cls.files["groups"][group_name][s]

    @classmethod
    def all_files(cls, group_name=None):
        if group_name != None:
            return [[v, k] for k, v in cls.files["groups"][group_name].items()]
        else:
            return [[v, k] for k, v in cls.files["files"].items()]

    @classmethod
    def group_count(cls):
        return len(cls.files["groups"])

    @classmethod
    def all_groups(cls):
        return [["Group: " + k, "%d files" % len(v)] for k, v in cls.files["groups"].items()]


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
        if create_favorite_list({"files": {}, "groups": {}}, True):
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
    def open_file(self, value, group=False):
        if value >= 0:
            if value < self.num_files or (group and value < self.num_files + 1):
                names = []
                if group:
                    if value == 0:
                        names = [self.files[x][1] for x in range(0, self.num_files)]
                    else:
                        names.append(self.files[value - 1][1])
                else:
                    names.append(self.files[value][1])

                for n in names:
                    if exists(n):
                        self.window.open_file(n)
                    else:
                        sublime.error_message("The following file does not exist:\n%s" % n)
            else:
                value -= self.num_files
                self.files = FileList.all_files(group_name=self.groups[value][0].replace("Group: ", "", 1))
                self.num_files = len(self.files)
                self.groups = []
                self.num_groups = 0
                if self.num_files:
                    self.window.show_quick_panel(
                        ["Open Group"] + self.files,
                        lambda x: self.open_file(x, group=True)
                    )
                else:
                    sublime.error_message("No favorites found! Try adding some.")

    def run(self):
        if not load_favorite_files():
            self.files = FileList.all_files()
            self.num_files = len(self.files)
            self.groups = FileList.all_groups()
            self.num_groups = len(self.groups)
            if self.num_files + self.num_groups > 0:
                self.window.show_quick_panel(
                    self.files + self.groups,
                    self.open_file
                )
            else:
                sublime.error_message("No favorites found! Try adding some.")


# Single add only
class AddFavoriteFileCommand(sublime_plugin.WindowCommand):
    def add(self, names, group_name=None):
        omit_count = 0
        disk_omit_count = 0
        added = 0
        for n in names:
            if not FileList.exists(n, group_name=group_name):
                if exists(n):
                    FileList.set(n, basename(n), group_name=group_name)
                    added += 1
                else:
                    disk_omit_count += 1
            else:
                omit_count += 1
        if added:
            create_favorite_list(FileList.files, True)
        if omit_count:
            sublime.error_message("%d file(s) already already present!" % omit_count)
        if disk_omit_count:
            message = "1 file does not exist on disk!" if disk_omit_count == 1 else "%d file(s) do not exist on disk!" % omit_count
            sublime.error_message(message)

    def create_group(self, value):
        repeat = False
        if value == "":
            sublime.error_message("Please provide a valid group name.")
            repeat = True
        elif FileList.exists(value, group=True):
            sublime.error_message("Group \"%s\" already exists.")
            repeat = True
        else:
            FileList.add_group(value)
            self.add(self.name, value)
        if repeat:
            self.window.show_input_panel(
                "Create Group: ",
                "New Group",
                self.create_group,
                None,
                None
            )

    def select_group(self, value):
        if value >= 0:
            self.add(self.name, self.groups[value][0].replace("Group: ", "", 1))

    def show_groups(self):
        self.groups = FileList.all_groups()
        self.window.show_quick_panel(
            self.groups,
            self.select_group
        )

    def group_answer(self, value):
        if value >= 0:
            if value == 0:
                self.add(self.name)
            elif value == 1:
                self.window.show_input_panel(
                    "Create Group: ",
                    "New Group",
                    self.create_group,
                    None,
                    None
                )
            elif value == 2:
                self.show_groups()
            else:
                sublime.error_message("Invalid Selection!")

    def group_prompt(self):
        self.group = ["No Group", "Create Group"]
        if FileList.group_count() > 0:
            self.group.append("Add to Group")

        self.window.show_quick_panel(
            self.group,
            self.group_answer
        )

    def file_answer(self, value):
        if value >= 0:
            view = self.window.active_view()
            if view != None:
                if value == 0:
                    name = view.file_name()
                    if name != None:
                        self.name.append(name)
                        self.group_prompt()
                if value == 1:
                    views = self.window.views()
                    if len(views) > 0:
                        for v in views:
                            name = v.file_name()
                            if name != None:
                                self.name.append(name)
                    if len(self.name) > 0:
                        self.group_prompt()
                if value == 2:
                    group, idx = self.window.get_view_index(view)
                    views = self.window.views_in_group(group)
                    if len(views) > 0:
                        for v in views:
                            name = v.file_name()
                            if name != None:
                                self.name.append(name)
                    if len(self.name) > 0:
                        self.group_prompt()

    def file_prompt(self, view_code):
        options = ["Add Current File to Favorites"]
        if view_code > 0:
            options.append("Add All Files to Favorites")
        if view_code > 1:
            options.append("Add All Files to in Active Group to Favorites")
        self.window.show_quick_panel(
            options,
            self.file_answer
        )

    def run(self):
        view = self.window.active_view()
        self.name = []
        if view != None:
            view_code = 0
            views = self.window.views()
            if len(views) > 1:
                view_code = 1
                if self.window.num_groups() > 1:
                    group, idx = self.window.get_view_index(view)
                    group_views = self.window.views_in_group(group)
                    if len(group_views) > 1:
                        view_code = 2
                self.file_prompt(view_code)
            else:
                name = view.file_name()
                if name != None:
                    self.name.append(name)
                    self.group_prompt()


class RemoveFavoriteFileCommand(sublime_plugin.WindowCommand):
    def remove(self, value, group=False, group_name=None):
        if value >= 0:
            if value < self.num_files or (group and value < self.num_files + 1):
                name = None
                if group:
                    if group_name == None:
                        return
                    if value == 0:
                        FileList.remove_group(group_name)
                        create_favorite_list(FileList.files, True)
                        return
                    else:
                        name = self.files[value - 1][1]
                else:
                    name = self.files[value][1]

                FileList.remove(name, group_name=group_name)
                create_favorite_list(FileList.files, True)
            else:
                value -= self.num_files
                group_name = self.groups[value][0].replace("Group: ", "", 1)
                self.files = FileList.all_files(group_name=group_name)
                self.num_files = len(self.files)
                self.groups = []
                self.num_groups = 0
                if self.num_files:
                    self.window.show_quick_panel(
                        ["Remove Group"] + self.files,
                        lambda x: self.remove(x, group=True, group_name=group_name)
                    )
                else:
                    sublime.error_message("No favorites found! Try adding some.")

    def run(self):
        if not load_favorite_files():
            self.files = FileList.all_files()
            self.num_files = len(self.files)
            self.groups = FileList.all_groups()
            self.num_groups = len(self.groups)
            if self.num_files + self.num_groups > 0:
                self.window.show_quick_panel(
                    self.files + self.groups,
                    self.remove
                )
            else:
                sublime.error_message("No favorites to remove!")


load_favorite_files(True)
