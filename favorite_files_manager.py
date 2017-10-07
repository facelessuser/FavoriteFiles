import sublime
import sublime_plugin
from os.path import join
import re
import json
import mdpopups

MANAGER_VIEW, SIZE, FILES, TEMP = None, None, {}, ""

CSS = """
div.mdpopups h1 {{
    font-size: 35px;
    font-weight: bold;
    font-style: italic;
    padding: {0}rem {1}rem {2}rem {3}rem;
    margin-bottom: 0.1rem;
    color:{4};
}}
"""

separator = "\n"+"_"*160+"\n"

no_help = '''
        [F1] open file/group        [F4] help       [F8] revert
        [F2] toggle auto-align      [F5] update     [Ctrl+Alt+Enter] finalize

'''

header = '''
In this view you can manage your favorite files and groups. You can:

    ▪ edit the aliases for your favorite files
    ▪ move entries between groups (best done with ctrl+shift+up/down)
    ▪ rename and delete groups
    ▪ create new groups and fill them with pairs alias/file path

Options explained:

    Open     :  open the file(s), also works with double-click and on groups
    Update   :  reload the view, to be sure everything went well.
    Revert   :  abort all your changes and reload from original file
    Finalize :  write the file, no undo possible

Toggle auto-align:

While in auto-align mode, the file paths will keep their alignment, but
multiple cursors are disabled, and it's advisable to toggle it off if deleting
whole lines or performing other operations that aren't simple renaming.

It's necessary that you respect formatting to avoid undesirable results:

    ▪ empty line before new groups, and only before new groups
    ▪ correct formatting for pairs {alias/file path}

         {alias}{spaces}{|}{spaces}{path}

    {spaces} is an arbitrary number of spaces, {|} is the vertical separator.

Be aware that if entries aren't formatted correctly can invalidate your whole
favorite files. So it's advisable to update the view, before finalizing,
unless you're sure of what you're doing.

If you create new groups, these must be followed by a semicolon, and they must
contain some entries. If you just copy and past them, they won't be retained
unless you modify them (both the group name and the entries).''' + "\n"*5


def pad_to(string, pad):
    '''Pad a string to n chars with spaces'''

    if len(string) > pad:
        return string[0:pad - 1] + u"…"

    pad = pad - len(string)
    string = "%s%s" % (string, " "*pad)
    return string


class FavoritesManager(sublime_plugin.TextCommand):
    def load_favs(self, from_temp):
        '''Create a table with aliases and corresponding file path'''

        if from_temp:
            data = json.loads(TEMP)
        else:
            with open(self.json_file) as f:
                data = json.load(f)

        aliases, groups, files = data['aliases'], data['groups'], data['files']
        files = [(aliases['files'][n], file) for n, file in enumerate(files)]
        g = {}
        for group in groups:
            g[group] = [(aliases['groups'][group][n], file)
                        for n, file in enumerate(data['groups'][group])]
        return (g, files)

    def render_view(self, edit, v, text, title="Favorite Files"):
        '''Render the Favorites Manager view'''

        v.set_scratch(True)
        v.set_name("✔ " + title)
        v.settings().set("gutter", False)
        v.settings().set("word_wrap", False)
        v.settings().set("margin", 30)
        syntax = "Packages/FavoriteFiles/FavoritesManager.sublime-syntax"
        scheme = "Packages/FavoriteFiles/FavoritesManager.hidden-tmTheme"
        v.settings().set("syntax", syntax)
        v.settings().set("color_scheme", scheme)
        v.insert(edit, 0, text)

        css = CSS.format(1, 2, 1, 10, "#A24141")
        mdpopups.add_phantom(
            v, "favman", sublime.Region(0, 0), "# Favorite Files",
            layout=sublime.LAYOUT_INLINE, css=css)
        v.show(1)

    def run(self, edit, help=False, from_temp=False):
        global MANAGER_VIEW, SIZE, HEADER, sets, auto_align

        w = sublime.active_window()
        self.json_file = join(sublime.packages_path(),
                              'User', 'favorite_files_list.json')

        # global auto_align can be toggled
        sets = sublime.load_settings("favorite_files.sublime-settings")
        auto_align = sets.get('manager_auto_align_as_you_type', False)

        # used by listener for comparison when it must be temporarily disabled
        FavoritesManagerListener.auto_align = auto_align

        text = header if help else no_help
        groups, files = self.load_favs(from_temp)

        # closing old and making new with different header
        if help:
            v = w.new_file()
            self.render_view(edit, v, text, title="Help")
            return
            # sublime.active_window().run_command('close_file')

        # better having some groups first so you know what you're doing
        if not groups:
            w.status_message("Please create at least a group before trying.")
            return

        text += "\nUngrouped favorite files:\n"
        HEADER = text   # store the current header for later removal

        # auto-align will start from this line
        nlines = HEADER.count("\n") - 1
        FavoritesManagerListener.nlines = nlines

        # loose favorite files
        for file in files:
            alias = pad_to(file[0], 40)
            text += alias+"|   "+file[1]+"\n"
            nlines += 1
            FILES[nlines] = file

        # groups
        for group in groups:
            nlines += 2
            group_line = nlines
            FILES[group_line] = []
            text += "\n"+group+":\n"
            for file in groups[group]:
                nlines += 1
                FILES[nlines] = file
                FILES[group_line].append(file)
                alias = pad_to(file[0], 40)
                text += alias+"|   "+file[1]+"\n"

        v = w.new_file()
        self.render_view(edit, v, text)
        MANAGER_VIEW = v
        SIZE = v.size()


class FavoritesManagerOpen(sublime_plugin.TextCommand):

    def run(self, edit):

        w = sublime.active_window()

        for i, sel in enumerate(self.view.sel()):
            line = self.view.rowcol(self.view.sel()[i].a)[0]
            if line not in FILES:
                return
            file = FILES[line][1]

            # it's a single file
            if type(file) == str:
                w.open_file(file)

            # it's a group
            else:
                for file in FILES[line]:
                    w.open_file(file[1])


class FavoritesManagerUpdate(sublime_plugin.TextCommand):

    def rebuild_json(self, action):
        global TEMP

        msg = ["Favorite Files: finalized",
               "Favorite Files: view updated",
               "Favorite Files: reverted changes"]

        data = {"aliases": self.aliases,
                "files": self.files,
                "groups": self.groups,
                "version": 1}

        w = sublime.active_window()
        w.run_command('close_file')

        if action == "finalize":
            with open(join(sublime.packages_path(
                      ), 'User', 'favorite_files_list.json'), "w") as f:
                json.dump(
                    data, f, sort_keys=True, indent=4, separators=(',', ': '))
            w.status_message(msg[0])

        elif action == "update":
            TEMP = json.dumps(data)
            self.view.run_command('favorites_manager', {"from_temp": True})
            w.status_message(msg[1])

        elif action == "revert":
            self.view.run_command('favorites_manager')
            w.status_message(msg[2])

    def remove_empty_lines(self):
        '''Removes empty lines, then looks for next group.'''
        empty = self.text[0] == "\n"
        if empty:
            self.text = self.text[1:]
            self.remove_empty_lines()
        else:
            self.search_groups()

    def search_groups(self):
        '''Looks for a group pattern, if found, calls search_files() with the
        group as argument.'''

        group_pat = re.compile(r"(.+):\n")
        group = group_pat.match(self.text)
        if group:
            group = group.groups()[0]
            self.groups[group] = []
            self.aliases['groups'][group] = []
            self.text = self.text.replace(group+":\n", "")
            self.search_files(group=group)

    def search_files(self, group=None):
        '''Looks for a file pattern, continues searching if it finds
        something, otherwise look for empty lines. If it's being called by
        search_groups(), it will have a 'group' argument.'''

        file_pat = re.compile(r"(.+)\| {0,}(.+)\n")
        file = file_pat.match(self.text)
        if file:
            alias, path = file.groups()
            alias = alias.rstrip()
            if not group:
                self.files.append(path)
                self.aliases['files'].append(alias)
            else:
                self.groups[group].append(path)
                self.aliases['groups'][group].append(alias)
            self.text = self.text.replace(file.group(), "")
            if self.text:
                self.search_files(group)
        else:
            self.remove_empty_lines()

    def run(self, edit, action="update"):

        if self.view != MANAGER_VIEW:
            return

        self.files, self.groups = [], {}
        self.aliases = {"files": [], "groups": {}}
        self.text = MANAGER_VIEW.substr(sublime.Region(0, MANAGER_VIEW.size()))

        self.text = self.text.replace(HEADER, "")        # remove header
        self.search_files()
        self.rebuild_json(action)

# ============================================================================

# below starts an experiment that needs some testing, but it seems to work
# rather well, trying to keep the table aligned as you modify it


class FavoritesManagerToggleAlign(sublime_plugin.TextCommand):

    def run(self, edit):
        global auto_align

        if auto_align:
            auto_align = False
            FavoritesManagerListener.auto_align = False
        else:
            auto_align = True
            FavoritesManagerListener.auto_align = True


class FavoritesManagerFixTable(sublime_plugin.TextCommand):

    def run(self, edit):
        global SIZE
        v = MANAGER_VIEW

        size = v.size()
        diff = SIZE - size
        line = v.line(v.sel()[0].a)
        within_separator = v.sel()[0].b < (line.a + 40)

        if within_separator and line.b - line.a > 40:
            if size > SIZE:
                point = line.a+40
                r = sublime.Region(point, point-diff)
                v.erase(edit, r)
            else:
                point = line.a+39
                string = " "*diff
                v.insert(edit, point, string)
            FavoritesManagerListener.skip = True

        SIZE = v.size()


class FavoritesManagerListener(sublime_plugin.EventListener):
    skip, nlines, auto_align = False, None, False

    def on_modified(self, view):
        global SIZE

        if MANAGER_VIEW:

            if not FavoritesManagerListener.auto_align:
                return

            # just modified, avoid recursions
            if FavoritesManagerListener.skip:
                FavoritesManagerListener.skip = False

            elif view == MANAGER_VIEW:
                if view.rowcol(view.sel()[0].a)[0] > self.nlines:
                    view.run_command('favorites_manager_fix_table')

    def on_selection_modified(self, view):
        '''Disallow multicursors and auto-align for multiline selection'''
        global SIZE

        if MANAGER_VIEW and view == MANAGER_VIEW:

            SIZE = view.size()
            sel = view.sel()[0]

            if auto_align:

                # disallow multicursor
                if len(view.sel()) > 1:
                    view.sel().clear()
                    view.sel().add(sel)

                # more than one line selected
                if sel.b > view.line(sel.a).b:
                    FavoritesManagerListener.auto_align = False

                # must still skip if at line beginning, not good
                elif not FavoritesManagerListener.auto_align:
                    if sel.a != view.line(sel.a).a:
                        FavoritesManagerListener.auto_align = True

    def on_text_command(self, view, command_name, args):
        global SIZE

        if MANAGER_VIEW and view == MANAGER_VIEW:
            SIZE = view.size()

            if command_name == 'drag_select' \
                    and 'by' in args and args['by'] == 'words':
                view.run_command('favorites_manager_open')
