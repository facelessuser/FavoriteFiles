'''
Favorite Files
Licensed under MIT
Copyright (c) 2012 Isaac Muse <isaacmuse@gmail.com>
'''

import re

# Comment types: lambda stripping function
comment_styles = {
    "c": lambda text, save_newlines=True: strip_comments_by_regex(
        # First group comments, second group non comments
        r"""(/\*[^*]*\*+(?:[^/*][^*]*\*+)*/|\s*//(?:[^\r\n])*)|("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|.[^/"']*)""",
        text, save_newlines
    ),
    "python": lambda text, save_newlines: strip_comments_by_regex(
        # First group comments, second group non comments
        r"""(\s*#(?:[^\r\n])*)|("{3}(?:\\.|[^\\])*"{3}|'{3}(?:\\.|[^\\])*'{3}|"(?:\\.|[^"\\])*"|'(?:\\.|[^'])*'|.[^#"']*)""",
        text, save_newlines
    )
}

# Additional styles that use the same style as others
comment_map = {
    "json": "c",  # Comments are not officially in the JSON spec, but if you strip them, you can use them
    "cpp": "c"
}


def strip_comments_by_regex(expression, text, spare_newlines=False):
    # If you want to remove comments, but keep the exact line_numbers
    def filter_comments(group, spare_newlines=False):
        if spare_newlines:
            regex = re.compile(r"\r?\n", re.MULTILINE)
            return ''.join([x[0] for x in regex.findall(group)])
        else:
            return ''

    return (
        ''.join(
            map(
                lambda m: m.group(2) if m.group(2) else filter_comments(m.group(1), spare_newlines),
                re.compile(expression, re.MULTILINE | re.DOTALL).finditer(text)
            )
        )
    )


def strip_comments(style, text, save_newlines=False):
    s = style.lower()
    func = None

    # Try to find specified comment, return none if cannot find
    if s in comment_styles:
        func = comment_styles[s]
    # Look for alternate mappings for existing remove functions
    elif s in comment_map:
        if comment_map[s] in comment_styles:
            func = comment_styles[comment_map[s]]

    # Exit if no suitable function could be found
    if func == None:
        return None

    return func(text, save_newlines)
