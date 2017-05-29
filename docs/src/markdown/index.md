# User Guide

## Overview
This is a simple plugin that was originally created to save favorite files that are not part of a project.  It can also be used to save and load groups of files which may be useful even for files part of a project.

Current features:

- Add/remove/open file(s) in favorites.
- Optionally store files in groups and open entire groups.
- Toggle project specific favorites.

## Commands
All commands are accessible via the command palette.

### Favorite Files: Open File
Provides a quick list to select one of your favorite files to open, or a group of favorite files.

### Favorite Files: Add File
Adds the current opened file, or all the files in the current window group, to your favorites.  An input panel will be opened so you can decide whether you want to save it normally or to a group.

### Favorite Files: Remove File
Remove a favorite file form your list or a group of favorite files.

### Favorite Files: Toggle Per Project
Allows saving per project favorites. Per projects must be toggled on for each project you are in.  You can toggle back and forth between per project and global favorites.  You cannot switch to per project favorites if you do not have a project file saved.  Save your current window configuration to a project file, and your per project favorites list will be saved in the same location.

!!!tip "Tip"
    If you have no need for per project favorites, you can completely disable the command in your settings file with the [enable_per_projects](#enable_per_projects) setting.

### Favorite Files: Clean Orphaned Favorites
Cleans out favorites in your list that no longer exist.

## Settings
Favorite files has only a couple of settings.

### enable_per_projects
Enables the per project toggling ability.  For more info, see: [Favorite Files: Toggle Per Project](#favorite-files-toggle-per-project).

```js
    // Enable ability for per project favorites .
    // Per Projects must be toggled on for each project you are in.
    // You can toggle back and forth between per project and global favorites.
    "enable_per_projects": true,
```

### use_sub_notify
Enables use of [SubNotify][subnotify] notifications.

```js
    // Use subnotify if available
    "use_sub_notify": true
```

--8<-- "refs.md"
