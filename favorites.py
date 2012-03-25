'''
Favorite Files
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
'''
import sublime
from os.path import exists, basename, getmtime, join, normpath
import json
import sys

lib = join(sublime.packages_path(), 'FavoriteFiles')
if not lib in sys.path:
    sys.path.append(lib)
from lib.file_strip.json import sanitize_json

FAVORITE_LIST_VERSION = 1


class FavObj:
    files = {}
    projects = set([])
    project_settings = {}
    last_access = 0
    global_file = ""
    file_name = ""


class FavProjects():
    @classmethod
    def add(cls, obj, win_id):
        obj.projects.add(win_id)

    @classmethod
    def remove(cls, obj, win_id):
        if cls.is_project_tracked(obj, win_id):
            obj.projects.remove(win_id)

    @classmethod
    def prune_projects(cls, obj):
        dead = obj.projects - set([x.id() for x in sublime.windows()])
        for key in dead:
            obj.projects.remove(key)

    @classmethod
    def is_project_tracked(cls, obj, win_id):
        return True if win_id != None and win_id in obj.projects else False

    @classmethod
    def is_project_enabled(cls, obj, win_id):
        enabled = cls.is_project_tracked(obj, win_id)
        if enabled:
            project = cls.get_project(win_id)
            # Make sure project is the new target
            if project != obj.file_name:
                obj.file_name = project
                obj.last_access = 0
            # If project does not exist
            # Revert to global
            if not exists(obj.file_name):
                obj.file_name = obj.global_file
                obj.last_access = 0
                obj.project_settings.clear()
                obj.projects.remove(win_id)
                enabled = False
        elif not FavFileMgr.is_global_file(obj):
            obj.file_name = obj.global_file
            obj.project_settings.clear()
            obj.last_access = 0
        return enabled

    @classmethod
    def has_project(cls, win_id):
        project = cls.get_project(win_id)
        return project != None

    @classmethod
    def get_project(cls, win_id):
        project = None
        reg_session = join(sublime.packages_path(), "..", "Settings", "Session.sublime_session")
        auto_save = join(sublime.packages_path(), "..", "Settings", "Auto Save Session.sublime_session")
        session = auto_save if exists(auto_save) else reg_session

        if not exists(session) or win_id == None:
            return project

        try:
            with open(session, 'r') as f:
                j = json.load(f)
                for w in j['windows']:
                    if w['window_id'] == win_id:
                        if "workspace_name" in w:
                            if sublime.platform() == "windows":
                                project = normpath(w["workspace_name"].lstrip("/").replace("/", ":/", 1))
                            else:
                                project = w["workspace_name"]
                            break
        except:
            pass
        return project


class FavFileMgr():
    @classmethod
    def is_global_file(cls, obj):
        return obj.file_name == obj.global_file

    @classmethod
    def update_list_format(cls, file_list):
        # TODO: remove this when enough time passes
        # Update list file from old format
        file_list["version"] = FAVORITE_LIST_VERSION
        file_list["files"] = [f for f in file_list["files"]]
        for g in file_list["groups"]:
            file_list["groups"][g] = [f for f in file_list["groups"][g]]

    @classmethod
    def clean_orphaned_favorites(cls, file_list):
        # Clean out dead links in global list and group lists
        # Remove empty groups
        file_list["files"] = [f for f in file_list["files"] if exists(f)]
        for g in file_list["groups"]:
            file_list["groups"][g] = [f for f in file_list["groups"][g] if exists(f)]
            if len(file_list["groups"][g]) == 0:
                del file_list["groups"][g]

    @classmethod
    def create_favorite_list(cls, obj, file_list, force=False):
        errors = False

        if not cls.is_global_file(obj):
            # For per project favorites write the project settings
            obj.project_settings['settings']['favorite_files'] = file_list
            l = obj.project_settings
        else:
            # For Globals, just write the favorites
            l = file_list

        if not exists(obj.file_name) or force:
            try:
                # Save as a JSON file
                j = json.dumps(l, sort_keys=True, indent=4, separators=(',', ': '))
                with open(obj.file_name, 'w') as f:
                    f.write(j + "\n")
                obj.last_access = getmtime(obj.file_name)
            except:
                sublime.error_message('Failed to write %s!' % basename(obj.file_name))
                errors = True
        return errors

    @classmethod
    def load_project_favorites(cls, obj, clean=False):
        errors = False
        try:
            with open(obj.file_name, "r") as f:
                # Allow C style comments and be forgiving of trailing commas
                content = sanitize_json(f.read(), True)
            j = json.loads(content)
            obj.project_settings = j
            if not "settings" in j:
                j['settings'] = {}
                file_list = {"version": 1, "files": [], "groups": {}}
                cls.create_favorite_list(obj, file_list, force=True)
            elif not "favorite_files" in j["settings"]:
                file_list = {"version": 1, "files": [], "groups": {}}
                cls.create_favorite_list(obj, file_list, force=True)
            else:
                file_list = j['settings']['favorite_files']
                if not "version" in file_list or file_list["version"] < FAVORITE_LIST_VERSION:
                    j['settings']['favorite_files'] = cls.update_list_format(file_list)
                    cls.create_favorite_list(obj, file_list, force=True)
                if clean:
                    j['settings']['favorite_files'] = cls.clean_orphaned_favorites(file_list)
                    cls.create_favorite_list(obj, file_list, force=True)
            # Update internal list and access times
            obj.last_access = getmtime(obj.file_name)
            obj.files = file_list
        except:
            errors = True
            sublime.error_message('Failed to load %s!' % basename(obj.file_name))
        return errors

    @classmethod
    def load_global_favorites(cls, obj, clean=False):
        errors = False
        try:
            with open(obj.file_name, "r") as f:
                # Allow C style comments and be forgiving of trailing commas
                content = sanitize_json(f.read(), True)
            file_list = json.loads(content)

            # TODO: remove this when enough time passes
            # Update version format
            if not "version" in file_list or file_list["version"] < FAVORITE_LIST_VERSION:
                cls.update_list_format(file_list)
                cls.create_favorite_list(obj, file_list, force=True)

            # Clean out dead links
            if clean:
                cls.clean_orphaned_favorites(file_list)
                cls.create_favorite_list(obj, file_list, force=True)

            # Update internal list and access times
            obj.last_access = getmtime(obj.file_name)
            obj.files = file_list
        except:
            errors = True
            sublime.error_message('Failed to load %s!' % basename(obj.file_name))
        return errors

    @classmethod
    def load_favorite_files(cls, obj, force=False, clean=False, win_id=None):
        errors = False

        # Is project enabled
        is_project = FavProjects.is_project_enabled(obj, win_id)

        if not exists(obj.file_name) and not is_project:
            # Create file list if it doesn't exist
            if cls.create_favorite_list(obj, {"version": 1, "files": [], "groups": {}}, force=True):
                sublime.error_message('Failed to cerate favorite_files_list.json!')
                errors = True
            else:
                force = True

        # Only reload if file has been written since last access (or if forced reload)
        if not errors and (force or getmtime(obj.file_name) != obj.last_access):
            if not is_project:
                errors = cls.load_global_favorites(obj, clean=clean)
            else:
                errors = cls.load_project_favorites(obj, clean=clean)
        return errors


class Favorites():
    def __init__(self, global_file):
        self.obj = FavObj()
        self.obj.global_file = global_file
        self.obj.last_access = 0
        self.obj.file_name = self.obj.global_file
        FavFileMgr.load_favorite_files(self.obj, force=True)

    def load(self, force=False, clean=False, win_id=None):
        return FavFileMgr.load_favorite_files(self.obj, force, clean, win_id)

    def save(self, force=False):
        return FavFileMgr.create_favorite_list(self.obj, self.obj.files, force=force)

    def toggle_per_projects(self, win_id):
        # Clean out closed windows
        FavProjects.prune_projects(self.obj)

        if FavProjects.is_project_tracked(self.obj, win_id):
            self.obj.projects.remove(win_id)
        else:
            if FavProjects.has_project(win_id):
                self.obj.projects.add(win_id)

    def remove_group(self, s):
        # Remove a group
        if self.exists(s, group=True):
            del self.obj.files["groups"][s]

    def add_group(self, s):
        # Add favorite group
        self.obj.files["groups"][s] = []

    def set(self, s, group_name=None):
        # Add file in global or group list
        if group_name == None:
            self.obj.files["files"].append(s)
        else:
            self.obj.files["groups"][group_name].append(s)

    def exists(self, s, group=False, group_name=None):
        if group:
            # See if group exists
            return True if s in self.obj.files["groups"] else False
        else:
            # See if file in global or group list exists
            if group_name == None:
                return True if s in set(self.obj.files["files"]) else False
            else:
                return True if s in set(self.obj.files["groups"][group_name]) else False

    def remove(self, s, group_name=None):
        # Remove file in group or global list
        if group_name == None:
            if self.exists(s):
                self.obj.files["files"].remove(s)
        else:
            if self.exists(s, group_name=group_name):
                self.obj.files["groups"][group_name].remove(s)

    def all_files(self, group_name=None):
        # Return all files in group or global list
        if group_name != None:
            return [[basename(path), path] for path in self.obj.files["groups"][group_name]]
        else:
            return [[basename(path), path] for path in self.obj.files["files"]]

    def group_count(self):
        # Return group count
        return len(self.obj.files["groups"])

    def all_groups(self):
        # Return all groups
        return [["Group: " + k, "%d files" % len(v)] for k, v in self.obj.files["groups"].items()]
