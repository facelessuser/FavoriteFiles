'''
Favorite Files
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
'''

import sublime
import sublime_plugin
from os.path import join, exists, basename, getmtime
import json
import sys

# Pull in included modules
lib = join(sublime.packages_path(), 'FavoriteFiles')
if not lib in sys.path:
    sys.path.append(lib)
from lib.file_strip.json import sanitize_json

FILES = join(sublime.packages_path(), 'User', 'favorite_files_list.json')

FAVORITE_LIST_VERSION = 1


class FileList:
    files = {}
    last_access = 0

    @classmethod
    def remove_group(cls, s):
        # Remove a group
        if cls.exists(s, group=True):
            del cls.files["groups"][s]

    @classmethod
    def add_group(cls, s):
        # Add favorite group
        cls.files["groups"][s] = []

    @classmethod
    def set(cls, s, group_name=None):
        # Add file in global or group list
        if group_name == None:
            cls.files["files"].append(s)
        else:
            cls.files["groups"][group_name].append(s)

    @classmethod
    def exists(cls, s, group=False, group_name=None):
        if group:
            # See if group exists
            return True if s in cls.files["groups"] else False
        else:
            # See if file in global or group list exists
            if group_name == None:
                return True if s in set(cls.files["files"]) else False
            else:
                return True if s in set(cls.files["groups"][group_name]) else False

    @classmethod
    def remove(cls, s, group_name=None):
        # Remove file in group or global list
        if group_name == None:
            if cls.exists(s):
                cls.files["files"].remove(s)
        else:
            if cls.exists(s, group_name=group_name):
                cls.files["groups"][group_name].remove(s)

    @classmethod
    def all_files(cls, group_name=None):
        # Return all files in group or global list
        if group_name != None:
            return [[basename(path), path] for path in cls.files["groups"][group_name]]
        else:
            return [[basename(path), path] for path in cls.files["files"]]

    @classmethod
    def group_count(cls):
        # Return group count
        return len(cls.files["groups"])

    @classmethod
    def all_groups(cls):
        # Return all groups
        return [["Group: " + k, "%d files" % len(v)] for k, v in cls.files["groups"].items()]


def update_list_format(file_list):
    # TODO: remove this when enough time passes
    # Update list file from old format
    file_list["version"] = FAVORITE_LIST_VERSION
    file_list["files"] = [f for f in file_list["files"]]
    for g in file_list["groups"]:
        file_list["groups"][g] = [f for f in file_list["groups"][g]]
    create_favorite_list(file_list, force=True)


def clean_orphaned_favorites(file_list):
    # Clean out dead links in global list and group lists
    # Remove empty groups
    file_list["files"] = [f for f in file_list["files"] if exists(f)]
    for g in file_list["groups"]:
        file_list["groups"][g] = [f for f in file_list["groups"][g] if exists(f)]
        if len(file_list["groups"][g]) == 0:
            del file_list["groups"][g]
    create_favorite_list(file_list, force=True)


def create_favorite_list(l, force=False):
    errors = False
    if not exists(FILES) or force:
        try:
            # Save as a JSON file
            j = json.dumps(l, sort_keys=True, indent=4, separators=(',', ': '))
            with open(FILES, 'w') as f:
                f.write(j + "\n")
            FileList.last_access = getmtime(FILES)
        except:
            sublime.error_message('Failed to create favorite_files_list.json!')
            errors = True
    return errors


def load_favorite_files(force=False, clean=False):
    errors = False
    if not exists(FILES):
        # Create file list if it doesn't exist
        if create_favorite_list({"version": 1, "files": [], "groups": {}}, True):
            sublime.error_message('Failed to cerate favorite_files_list.json!')
            errors = True
        else:
            force = True

    # Only reload if file has been written since last access (or if forced reload)
    if not errors and (force or getmtime(FILES) != FileList.last_access):
        try:
            with open(FILES, "r") as f:
                # Allow C style comments and be forgiving of trailing commas
                content = sanitize_json(f.read(), True)
            file_list = json.loads(content)

            # TODO: remove this when enough time passes
            # Update version format
            if not "version" in file_list or file_list["version"] < FAVORITE_LIST_VERSION:
                update_list_format(file_list)

            # Clean out dead links
            if clean:
                clean_orphaned_favorites(file_list)

            # Update internal list and access times
            FileList.last_access = getmtime(FILES)
            FileList.files = file_list
        except:
            errors = True
            sublime.error_message('Failed to read favorite_files_list.json!')
    return errors


class CleanOrphanedFavoritesCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        # Clean out all dead links
        load_favorite_files(force=True, clean=True)


class SelectFavoriteFileCommand(sublime_plugin.WindowCommand):
    def open_file(self, value, group=False):
        if value >= 0:
            active_group = self.window.active_group()
            if value < self.num_files or (group and value < self.num_files + 1):
                # Open global file, file in group, or all fiels in group
                names = []
                if group:
                    if value == 0:
                        # Open all files in group
                        names = [self.files[x][1] for x in range(0, self.num_files)]
                    else:
                        # Open file in group
                        names.append(self.files[value - 1][1])
                else:
                    # Open global file
                    names.append(self.files[value][1])

                # Iterate through file list ensure they load in proper view index order
                count = 0
                for n in names:
                    if exists(n):
                        view = self.window.open_file(n)
                        if view != None:
                            if active_group >= 0:
                                self.window.set_view_index(view, active_group, count)
                            count += 1

                    else:
                        sublime.error_message("The following file does not exist:\n%s" % n)
            else:
                # Decend into group
                value -= self.num_files
                self.files = FileList.all_files(group_name=self.groups[value][0].replace("Group: ", "", 1))
                self.num_files = len(self.files)
                self.groups = []
                self.num_groups = 0

                # Show files in group
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


class AddFavoriteFileCommand(sublime_plugin.WindowCommand):
    def add(self, names, group_name=None):
        disk_omit_count = 0
        added = 0
        # Iterate names and add them to group/global if not already added
        for n in names:
            if not FileList.exists(n, group_name=group_name):
                if exists(n):
                    FileList.set(n, group_name=group_name)
                    added += 1
                else:
                    # File does not exist on disk; cannot add
                    disk_omit_count += 1
        if added:
            # Save if files were added
            create_favorite_list(FileList.files, True)
        if disk_omit_count:
            # Alert that files could be added
            message = "1 file does not exist on disk!" if disk_omit_count == 1 else "%d file(s) do not exist on disk!" % disk_omit_count
            sublime.error_message(message)

    def create_group(self, value):
        repeat = False
        if value == "":
            # Require an actual name
            sublime.error_message("Please provide a valid group name.")
            repeat = True
        elif FileList.exists(value, group=True):
            # Do not allow duplicates
            sublime.error_message("Group \"%s\" already exists.")
            repeat = True
        else:
            # Add group
            FileList.add_group(value)
            self.add(self.name, value)
        if repeat:
            # Ask again if name was not sufficient
            self.window.show_input_panel(
                "Create Group: ",
                "New Group",
                self.create_group,
                None,
                None
            )

    def select_group(self, value, replace=False):
        if value >= 0:
            group_name = self.groups[value][0].replace("Group: ", "", 1)
            if replace:
                # Start with empty group for "Replace Group" selection
                FileList.add_group(group_name)
            # Add favorites
            self.add(self.name, group_name)

    def show_groups(self, replace=False):
        # Show availabe groups
        self.groups = FileList.all_groups()
        self.window.show_quick_panel(
            self.groups,
            lambda x: self.select_group(x, replace=replace)
        )

    def group_answer(self, value):
        if value >= 0:
            if value == 0:
                # No group; add file to favorites
                self.add(self.name)
            elif value == 1:
                # Request new group name
                self.window.show_input_panel(
                    "Create Group: ",
                    "New Group",
                    self.create_group,
                    None,
                    None
                )
            elif value == 2:
                # "Add to Group"
                self.show_groups()
            elif value == 3:
                # "Replace Group"
                self.show_groups(replace=True)

    def group_prompt(self):
        # Default options
        self.group = ["No Group", "Create Group"]
        if FileList.group_count() > 0:
            # Options if groups already exit
            self.group += ["Add to Group", "Replace Group"]

        # Present group options
        self.window.show_quick_panel(
            self.group,
            self.group_answer
        )

    def file_answer(self, value):
        if value >= 0:
            view = self.window.active_view()
            if view != None:
                if value == 0:
                    # Single file
                    name = view.file_name()
                    if name != None:
                        self.name.append(name)
                        self.group_prompt()
                if value == 1:
                    # All files in window
                    views = self.window.views()
                    if len(views) > 0:
                        for v in views:
                            name = v.file_name()
                            if name != None:
                                self.name.append(name)
                    if len(self.name) > 0:
                        self.group_prompt()
                if value == 2:
                    # All files in layout group
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
        # Add current active file
        options = ["Add Current File to Favorites"]
        if view_code > 0:
            # Add all files in window
            options.append("Add All Files to Favorites")
        if view_code > 1:
            # Add all files in layout group
            options.append("Add All Files to in Active Group to Favorites")

        # Preset file options
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

            # If there is more than one view open allow saving all views
            # TODO: Widget views probably show up here too, maybe look into exclduing them
            if len(views) > 1:
                view_code = 1
                # See if there is more than one group; if so allow saving of a specific group
                if self.window.num_groups() > 1:
                    group, idx = self.window.get_view_index(view)
                    group_views = self.window.views_in_group(group)
                    if len(group_views) > 1:
                        view_code = 2
                self.file_prompt(view_code)
            else:
                # Only single file open, proceed without file options
                name = view.file_name()
                if name != None:
                    self.name.append(name)
                    self.group_prompt()


class RemoveFavoriteFileCommand(sublime_plugin.WindowCommand):
    def remove(self, value, group=False, group_name=None):
        if value >= 0:
            # Remove file from global, file from group list, or entire group
            if value < self.num_files or (group and value < self.num_files + 1):
                name = None
                if group:
                    if group_name == None:
                        return
                    if value == 0:
                        # Remove group
                        FileList.remove_group(group_name)
                        create_favorite_list(FileList.files, True)
                        return
                    else:
                        # Remove group file
                        name = self.files[value - 1][1]
                else:
                    # Remove global file
                    name = self.files[value][1]

                # Remove file and save
                FileList.remove(name, group_name=group_name)
                create_favorite_list(FileList.files, True)
            else:
                # Decend into group
                value -= self.num_files
                group_name = self.groups[value][0].replace("Group: ", "", 1)
                self.files = FileList.all_files(group_name=group_name)
                self.num_files = len(self.files)
                self.groups = []
                self.num_groups = 0
                # Show group files
                if self.num_files:
                    self.window.show_quick_panel(
                        ["Remove Group"] + self.files,
                        lambda x: self.remove(x, group=True, group_name=group_name)
                    )
                else:
                    sublime.error_message("No favorites found! Try adding some.")

    def run(self):
        if not load_favorite_files():
            # Present both files and groups for removal
            self.files = FileList.all_files()
            self.num_files = len(self.files)
            self.groups = FileList.all_groups()
            self.num_groups = len(self.groups)

            # Show panel
            if self.num_files + self.num_groups > 0:
                self.window.show_quick_panel(
                    self.files + self.groups,
                    self.remove
                )
            else:
                sublime.error_message("No favorites to remove!")


load_favorite_files(True)
