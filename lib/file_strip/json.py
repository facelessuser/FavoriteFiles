'''
Favorite Files
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
'''

import re
import comments


def strip_dangling_comments(text, save_newlines=False):
    regex = re.compile(
        # ([1st group] dangling commas) | ([8th group] everything else)
        r"""((,([\s\r\n]*)(\]))|(,([\s\r\n]*)(\})))|("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|.[^,"']*)""",
        re.MULTILINE | re.DOTALL
    )

    def remove_comma(m, spare_newlines=False):
        if spare_newlines:
            if m.group(2):
                # ,] -> ]
                return m.group(3) + m.group(4)
            else:
                # ,} -> }
                return m.group(6) + m.group(7)
        else:
            # ,] -> ] else ,} -> }
            return m.group(4) if m.group(2) else m.group(7)

    return (
        ''.join(
            map(
                lambda m: m.group(8) if m.group(8) else remove_comma(m, save_newlines),
                regex.finditer(text)
            )
        )
    )


def strip_comments(text, save_newlines):
    return strip_comments('json', text, save_newlines)


def sanitize_json(text, save_newlines=False):
    return strip_dangling_comments(comments.strip_comments('json', text, save_newlines), save_newlines)
