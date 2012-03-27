'''
Favorite Files
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
'''
import sublime
from os.path import exists, basename, getmtime, join, normpath, splitext
import json
import sys
import re

lib = join(sublime.packages_path(), 'FavoriteFiles')
if not lib in sys.path:
    sys.path.append(lib)
from lib.file_strip.json import sanitize_json

FAVORITE_LIST_VERSION = 1


class FavObj:
    files = {}
    projects = set([])
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
    def project_adjust(cls, obj, win_id, force=False):
        enabled = cls.is_project_tracked(obj, win_id)
        if enabled:
            project = cls.get_project(win_id)
            if project != None:
                project_favs = splitext(project)[0] + "-favs.json"
            if not exists(project_favs) and not force:
                sublime.error_message('Cannot find favorite list!\nProject name probably changed.\nSwitching to global list.')
                obj.projects.remove(win_id)
                obj.file_name = obj.global_file
                obj.last_access = 0
            # Make sure project is the new target
            if project_favs != obj.file_name:
                obj.file_name = project_favs
                obj.last_access = 0
        elif not FavFileMgr.is_global_file(obj):
            obj.file_name = obj.global_file
            obj.last_access = 0
        return enabled

    @classmethod
    def has_project(cls, win_id):
        project = cls.get_project(win_id)
        return True if project != None else False

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
                # Tabs in strings messes things up for some reason
                j = json.loads(f.read().replace('\t', " "))
                for w in j['windows']:
                    if w['window_id'] == win_id:
                        if "workspace_name" in w:
                            if sublime.platform() == "windows":
                                # Account for windows specific formatting
                                project = normpath(w["workspace_name"].lstrip("/").replace("/", ":/", 1))
                            else:
                                project = w["workspace_name"]
                            break
        except:
            pass

        # Throw out empty project names
        if project == None or re.match(".*\\.sublime-project", project) == None or not exists(project):
            project = None

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

        if not exists(obj.file_name) or force:
            try:
                # Save as a JSON file
                j = json.dumps(file_list, sort_keys=True, indent=4, separators=(',', ': '))
                with open(obj.file_name, 'w') as f:
                    f.write(j + "\n")
                obj.last_access = getmtime(obj.file_name)
            except:
                sublime.error_message('Failed to write %s!' % basename(obj.file_name))
                errors = True
        return errors

    @classmethod
    def load_favorites(cls, obj, clean=False):
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
            if cls.is_global_file():
                sublime.error_message('Failed to load %s!' % basename(obj.file_name))
            else:
                sublime.error_message(
                    'Failed to load %s!\nDid you rename your project?\nTry toggling "Per Projects" off and on and try again.' % basename(obj.file_name)
                )
        return errors

    @classmethod
    def load_favorite_files(cls, obj, force=False, clean=False, win_id=None):
        errors = False

        # Is project enabled
        FavProjects.project_adjust(obj, win_id, force)

        if not exists(obj.file_name):
            if force:
                # Create file list if it doesn't exist
                if cls.create_favorite_list(obj, {"version": 1, "files": [], "groups": {}}, force=True):
                    sublime.error_message('Failed to cerate %s!' % basename(obj.file_name))
                    errors = True
                else:
                    force = True
            else:
                errors = True

        # Only reload if file has been written since last access (or if forced reload)
        if not errors and (force or getmtime(obj.file_name) != obj.last_access):
            errors = cls.load_favorites(obj, clean=clean)
        return errors


class Favorites():
    def __init__(self, global_file):
        self.obj = FavObj()
        self.obj.global_file = global_file
        self.obj.last_access = 0
        self.obj.file_name = self.obj.global_file
        self.open(self.obj)

    def open(self, win_id=None):
        return FavFileMgr.load_favorite_files(self.obj, force=True, win_id=win_id)

    def load(self, force=False, clean=False, win_id=None):
        return FavFileMgr.load_favorite_files(self.obj, force, clean, win_id)

    def save(self, force=False):
        return FavFileMgr.create_favorite_list(self.obj, self.obj.files, force=force)

    def toggle_global(self, win_id):
        errors = False
        # Clean out closed windows
        FavProjects.prune_projects(self.obj)

        if FavProjects.is_project_tracked(self.obj, win_id):
            self.obj.projects.remove(win_id)
        else:
            errors = True
        return errors

    def toggle_per_projects(self, win_id):
        errors = False

        if FavProjects.has_project(win_id):
            self.obj.projects.add(win_id)
        else:
            errors = True
        return errors

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
