import sublime
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except:
    class Notify:
        @classmethod
        def is_ready(cls):
            return False


def notify(msg):
    settings = sublime.load_settings("favorite_files.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "FavoriteFiles", "msg": msg})
    else:
        sublime.status_message(msg)


def error(msg):
    settings = sublime.load_settings("favorite_files.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "FavoriteFiles", "msg": msg, "level": "error"})
    else:
        sublime.error_message("FavoriteFiles:\n%s" % msg)
