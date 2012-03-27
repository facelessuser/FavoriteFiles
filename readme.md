# About
This is a simple plugin to save favorite files that are not part of a project.  It supports adding and removing favorites and open favorite files.

# Usage
All commands are accessible via the command palatte.

## Favorite Files: Open File
Command provides a quick list to select one of your favorite files to open.

## Favorite Files: Add File
Add the current opened file to your favorites.  An input panel will be opened so you can provide a unique name for your favorite file.

## Favorite Files: Remove File
Remove a favorite file form your list.

# License

Favorite Files is released under the MIT license.

Copyright (c) 2011 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Version 0.5.3
- Catch project rename when when opening or removing items from list (will only catch after a file has been saved).

# Version 0.5.2
- Rework logic to catch renamed projects
- Strip tabs from session which can break the parsing

# Version 0.5.1
- More explicit match for finding project files

# Version 0.5.0
- Abandon storing favs in project settings file, but store the settings in a file in the same directory as project settings.
- Force refresh of session if project cannot be found and try to locate project again.

# Version 0.4.0
- Added code to support per project favorites (disabled by default due to circumstances where project cannot be determined)

# Version 0.3.1
- Open files in active group

# Version 0.3.0
- Ensure favorites are opened in order they were saved
- Add option to replace group
- Remove dialogs alerting user that files already existed in favorites

# Version 0.2.1
- Use lists for favorite files instead of dictionary
- Add format version to favorite file list so format can be updated if needed in the future
- Add command for cleaning out orphaned favorites

# Version 0.2.0
- File list now reloads on modification only
- File list is forgiving if modified by hand
- Fix issues with canceling quick list
- Added groups
- favorite_files.json renamed to favorite_files_list.json (new format)

# Version 0.1.0
- First release
