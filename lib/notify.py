"""
Favorite Files SubNotify support.

Licensed under MIT
Copyright (c) 2012 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except Exception:
    class Notify:

        """Notify fallback class."""

        @classmethod
        def is_ready(cls):
            """Return false to disable SubNotify support."""

            return False


def notify(msg):
    """Notify message."""

    settings = sublime.load_settings("favorite_files.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "FavoriteFiles", "msg": msg})
    else:
        sublime.status_message(msg)


def error(msg):
    """Error message."""

    settings = sublime.load_settings("favorite_files.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "FavoriteFiles", "msg": msg, "level": "error"})
    else:
        sublime.error_message("FavoriteFiles:\n%s" % msg)
