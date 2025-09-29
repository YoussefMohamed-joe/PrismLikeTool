### Architecture Overview

Prism is a DCC-agnostic pipeline toolkit. It is built around a core application with plugin-based integrations for DCCs (Maya, Blender, Houdini, Nuke, Photoshop, etc.).

- Core entry points: `Scripts/PrismCore.py` (launcher), `Scripts/PrismTray.py` (system tray), `Scripts/PrismSettings.py` (settings UI).
- Utilities: under `Scripts/PrismUtils/` for plugins, paths, products, media, projects, users, and UI helpers.
- Plugins: under `Plugins/` (built-in Apps and Custom); user/computer/project plugins are resolved at runtime via `PluginManager`.
- UI: Most dialogs and widgets are PySide/PyQt via `qtpy` compatibility layer with `.ui` files in `Scripts/UserInterfacesPrism` and various plugin-specific UI folders.

Key flows:
- Startup: Core loads app plugin and custom plugins via `PluginManager.initializePlugins`, then triggers app-specific startup hooks.
- Tray: `PrismTray` exposes quick actions (Project Browser, Settings, Open folders) and listens on a local socket for single-instance behavior.
- Settings: `PrismSettings` aggregates User and Project settings; provides plugin management and DCC integration management.
- Paths: `PathManager` resolves project structure templates and provides location-aware path conversions (global/local/custom locations).
- Integrations: `Integration` persists installation paths and delegates per-app integration install/uninstall to the respective app plugin.

Data/config:
- Project config (`.yml/.json`) accessed via core `getConfig/setConfig` helpers.
- User config (`userini`) for username, preferences, plugin autoload list, etc.
- Version info files accompanying products/renders to track provenance and metadata.

Extensibility:
- New App plugin: create plugin folder from `PluginEmpty` preset, implement init/variables/functions modules, and (optionally) integration.
- Custom plugins: add pipeline features, UI, and callbacks; register via `PluginManager` and optionally expose settings.


