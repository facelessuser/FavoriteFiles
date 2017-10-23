"""
Favorite Files.

Licensed under MIT
Copyright (c) 2012 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""

import sublime
import sublime_plugin
import os
import re
from FavoriteFiles.favorites import Favorites
from FavoriteFiles.lib.notify import error

Favs = None

RE_ALIAS = re.compile(r'^[\w\d\- \.]*$', re.UNICODE)


class FavoriteFilesCleanOrphansCommand(sublime_plugin.WindowCommand):
    """Clean out favorties that no longer exist."""

    def run(self):
        """Run the command."""

        # Clean out all dead links
        if not Favs.load(clean=True, win_id=self.window.id()):
            Favs.load(force=True, clean=True, win_id=self.window.id())


class FavoriteFilesEditAliasCommand(sublime_plugin.WindowCommand):
    """Open the selected favorite(s)."""

    def edit_alias(self, value, group=False):
        """Edit alias."""

        if value == -1:
            return

        if value >= 0:
            if value < self.num_files or (group and value < self.num_files + 1):
                # Open global file, file in group, or all files in group
                name = self.files[value][0]

                self.current_index = value
                self.window.show_input_panel("Alias:", name, self.apply_alias, None, None)
            else:
                # Decend into group
                value -= self.num_files
                self.group_name = self.groups[value][0].replace("Group: ", "", 1)
                self.files = Favs.all_files(group_name=self.group_name)
                self.num_files = len(self.files)
                self.groups = []
                self.num_groups = 0

                # Show files in group
                if self.num_files:
                    self.window.show_quick_panel(
                        self.files,
                        lambda x: self.edit_alias(x, group=True)
                    )
                else:
                    error("No favorites found! Try adding some.")

    def apply_alias(self, value):
        """Apply alias."""

        if value is not None:
            valid = RE_ALIAS.match(value) is not None
            length = len(value) <= 40
            if valid and length:
                Favs.set_alias(value.strip(), self.current_index, self.group_name)
            else:
                if not valid:
                    error("Alias must contain only Unicode word characters, numbers, spaces, hyphens, and periods!")
                else:
                    error("Alias cannot be greater than 40 characters!")
                self.window.show_input_panel("Alias:", value, self.apply_alias, None, None)

    def run(self):
        """Run the command."""

        if not Favs.load(win_id=self.window.id()):
            self.files = Favs.all_files()
            self.num_files = len(self.files)
            self.groups = Favs.all_groups()
            self.num_groups = len(self.groups)
            # initialize group to None, will be set if descending into a group
            self.group_name = None
            if self.num_files + self.num_groups > 0:
                self.window.show_quick_panel(
                    self.files + self.groups,
                    self.edit_alias
                )
            else:
                error("No favorites found! Try adding some.")


class FavoriteFilesOpenCommand(sublime_plugin.WindowCommand):
    """Open the selected favorite(s)."""

    def open_file(self, value, group=False):
        """Open the file(s)."""

        if value == -1:
            return

        if value >= 0:
            active_group = self.window.active_group()
            if value < self.num_files or (group and value < self.num_files + 1):
                # Open global file, file in group, or all files in group
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
                focus_view = None

                for n in names:
                    if os.path.exists(n):
                        view = self.window.open_file(n)
                        if view is not None:
                            focus_view = view
                            if active_group >= 0:
                                self.window.set_view_index(view, active_group, count)
                            count += 1
                    else:
                        error("The following file does not exist:\n%s" % n)
                if focus_view is not None:
                    # Horrible ugly hack to ensure opened file gets focus
                    def fn(focus_view):
                        """Ensure focus of view."""
                        self.window.focus_view(focus_view)
                        self.window.show_quick_panel(["None"], None)
                        self.window.run_command("hide_overlay")
                    sublime.set_timeout(lambda: fn(focus_view), 500)
            else:
                # Decend into group
                value -= self.num_files
                self.files = Favs.all_files(group_name=self.groups[value][0].replace("Group: ", "", 1))
                self.num_files = len(self.files)
                self.groups = []
                self.num_groups = 0

                # Show files in group
                if self.num_files:
                    self.window.show_quick_panel(
                        [["Open Group", ""]] + self.files,
                        lambda x: self.open_file(x, group=True)
                    )
                else:
                    error("No favorites found! Try adding some.")

    def run(self):
        """Run the command."""

        if not Favs.load(win_id=self.window.id()):
            self.files = Favs.all_files()
            self.num_files = len(self.files)
            self.groups = Favs.all_groups()
            self.num_groups = len(self.groups)
            if self.num_files + self.num_groups > 0:
                self.window.show_quick_panel(
                    self.files + self.groups,
                    self.open_file
                )
            else:
                error("No favorites found! Try adding some.")


class FavoriteFilesAddCommand(sublime_plugin.WindowCommand):
    """Add favorite(s) to the global group or the specified group."""

    def prompt_for_alias(self, name, group_name=None):
        """Prompt for an alias for the favorite file."""

        index = None
        files = Favs.obj.files['groups'][group_name] if group_name is not None else Favs.obj.files['files']

        for idx, f in enumerate(files):
            if f['alias'] == name:
                index = idx
                break

        if index is not None:
            self.current_index = index
            self.group_name = group_name

        self.window.show_input_panel("Alias:", name, self.apply_alias, None, None)

    def apply_alias(self, value):
        """Apply alias."""

        if value is not None:
            valid = RE_ALIAS.match(value) is not None
            length = len(value) <= 40
            if valid and length:
                Favs.set_alias(value.strip(), self.current_index, self.group_name)
            else:
                if not valid:
                    error("Alias must contain only Unicode word characters, numbers, spaces, hyphens, and periods!")
                else:
                    error("Alias cannot be greater than 40 characters!")
                self.window.show_input_panel("Alias:", value, self.apply_alias, None, None)

    def add(self, names, group_name=None):
        """Add favorites."""

        disk_omit_count = 0
        added = 0
        # Iterate names and add them to group/global if not already added
        for n in names:
            if Favs.file_index(n, group_name=group_name) is None:
                if os.path.exists(n):
                    Favs.set(n, group_name=group_name)
                    added += 1
                else:
                    # File does not exist on disk; cannot add
                    disk_omit_count += 1
        if added:
            # Save if files were added
            Favs.save(True)
            if len(names) == 1 and settings().get('always_ask_alias', False):
                self.prompt_for_alias(os.path.basename(names[0]), group_name)

        if disk_omit_count:
            # Alert that files could be added
            if disk_omit_count == 1:
                message = "1 file does not exist on disk!"
            else:
                message = "%d file(s) do not exist on disk!" % disk_omit_count
            error(message)

    def create_group(self, value):
        """Create the specified group."""

        repeat = False
        if value == "":
            # Require an actual name
            error("Please provide a valid group name.")
            repeat = True
        elif Favs.group_exists(value):
            # Do not allow duplicates
            error("Group \"%s\" already exists." % value)
            repeat = True
        else:
            # Add group
            Favs.add_group(value)
            self.add(self.name, value)
        if repeat:
            # Ask again if name was not sufficient
            v = self.window.show_input_panel(
                "Create Group: ",
                "New Group",
                self.create_group,
                None,
                None
            )
            v.run_command("select_all")

    def select_group(self, value, replace=False):
        """Add favorite to the group."""

        if value >= 0:
            group_name = self.groups[value][0].replace("Group: ", "", 1)
            if replace:
                # Start with empty group for "Replace Group" selection
                Favs.add_group(group_name)
            # Add favorites
            self.add(self.name, group_name)

    def show_groups(self, replace=False):
        """Prompt user with stored groups."""

        # Show availabe groups
        self.groups = Favs.all_groups()
        self.window.show_quick_panel(
            self.groups,
            lambda x: self.select_group(x, replace=replace)
        )

    def group_answer(self, value):
        """Handle the user's 'group' options answer."""

        if value >= 0:
            if value == 0:
                # No group; add file to favorites
                self.add(self.name)
            elif value == 1:
                # Request new group name
                v = self.window.show_input_panel(
                    "Create Group: ",
                    "New Group",
                    self.create_group,
                    None,
                    None
                )
                v.run_command("select_all")
            elif value == 2:
                # "Add to Group"
                self.show_groups()
            elif value == 3:
                # "Replace Group"
                self.show_groups(replace=True)

    def group_prompt(self):
        """Prompt user with 'group' options."""

        # Default options
        self.group = ["No Group", "Create Group"]
        if Favs.group_count() > 0:
            # Options if groups already exit
            self.group += ["Add to Group", "Replace Group"]

        self.window.show_quick_panel(
            self.group,
            self.group_answer
        )

    def file_answer(self, value):
        """Handle the user's 'add' option selection."""

        if value >= 0:
            view = self.window.active_view()
            if view is not None:
                if value == 0:
                    # Single file
                    name = view.file_name()
                    if name is not None:
                        self.name.append(name)
                        self.group_prompt()
                if value == 1:
                    # All files in window
                    views = self.window.views()
                    if len(views) > 0:
                        for v in views:
                            name = v.file_name()
                            if name is not None:
                                self.name.append(name)
                    if len(self.name) > 0:
                        self.group_prompt()
                if value == 2:
                    # All files in layout group
                    group = self.window.get_view_index(view)[0]
                    views = self.window.views_in_group(group)
                    if len(views) > 0:
                        for v in views:
                            name = v.file_name()
                            if name is not None:
                                self.name.append(name)
                    if len(self.name) > 0:
                        self.group_prompt()

    def file_prompt(self, view_code):
        """Prompt the user for 'add' options."""

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
        """Run the command."""

        view = self.window.active_view()
        self.name = []

        if view is not None:
            view_code = 0
            views = self.window.views()

            # If there is more than one view open allow saving all views
            # TODO: Widget views probably show up here too, maybe look into exclduing them
            if len(views) > 1:
                view_code = 1
                # See if there is more than one group; if so allow saving of a specific group
                if self.window.num_groups() > 1:
                    group = self.window.get_view_index(view)[0]
                    group_views = self.window.views_in_group(group)
                    if len(group_views) > 1:
                        view_code = 2
                self.file_prompt(view_code)
            else:
                # Only single file open, proceed without file options
                name = view.file_name()
                if name is not None:
                    self.name.append(name)
                    self.group_prompt()


class FavoriteFilesRemoveCommand(sublime_plugin.WindowCommand):
    """Remove the file favorites from the tracked list."""

    def remove(self, value, group=False, group_name=None):
        """Remove the favorite(s)."""

        if value >= 0:
            # Remove file from global, file from group list, or entire group
            if value < self.num_files or (group and value < self.num_files + 1):
                name = None
                if group:
                    if group_name is None:
                        return
                    if value == 0:
                        # Remove group
                        Favs.remove_group(group_name)
                        Favs.save(True)
                        return
                    else:
                        # Remove group file
                        name = self.files[value - 1][1]
                else:
                    # Remove global file
                    name = self.files[value][1]

                # Remove file and save
                Favs.remove(name, group_name=group_name)
                Favs.save(True)
            else:
                # Decend into group
                value -= self.num_files
                group_name = self.groups[value][0].replace("Group: ", "", 1)
                self.files = Favs.all_files(group_name=group_name)
                self.num_files = len(self.files)
                self.groups = []
                self.num_groups = 0
                # Show group files
                if self.num_files:
                    self.window.show_quick_panel(
                        [["Remove Group", ""]] + self.files,
                        lambda x: self.remove(x, group=True, group_name=group_name)
                    )
                else:
                    error("No favorites found! Try adding some.")

    def run(self):
        """Run the command."""

        if not Favs.load(win_id=self.window.id()):
            # Present both files and groups for removal
            self.files = Favs.all_files()
            self.num_files = len(self.files)
            self.groups = Favs.all_groups()
            self.num_groups = len(self.groups)

            # Show panel
            if self.num_files + self.num_groups > 0:
                self.window.show_quick_panel(
                    self.files + self.groups,
                    self.remove
                )
            else:
                error("No favorites to remove!")


class FavoriteFilesTogglePerProjectCommand(sublime_plugin.WindowCommand):
    """Toggle per project favorites."""

    def run(self):
        """Run the command."""
        win_id = self.window.id()

        # Try and toggle back to global first
        if not Favs.toggle_global(win_id):
            return

        # Try and toggle per project
        if Favs.toggle_per_projects(win_id):
            error('Could not find a project file!')
        else:
            Favs.open(win_id=self.window.id())

    def is_enabled(self):
        """Check if command is enabled."""

        return settings().get("enable_per_projects", False)


def check_st_version():
    """Check the Sublime version."""

    if int(sublime.version()) < 3080:
        window = sublime.active_window()
        if window is not None:
            window.run_command('open_file', {"file": "${packages}/FavoriteFiles/messages/upgrade-st-3080.md"})


def settings():
    """Return settings file."""
    return sublime.load_settings("favorite_files.sublime-settings")


def plugin_loaded():
    """Setup plugin."""

    global Favs
    Favs = Favorites(os.path.join(sublime.packages_path(), 'User', 'favorite_files_list.json'))
    check_st_version()
