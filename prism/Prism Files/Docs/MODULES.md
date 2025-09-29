### Key Modules

- Scripts/PrismTray.py
  - Provides the system tray icon, context menu, and single-instance communication.
  - Starts the Project Browser and opens Settings.

- Scripts/PrismSettings.py
  - Dialog aggregating User and Project settings.
  - Manages plugin load/unload, autoload, search paths, and DCC integration paths.

- Scripts/PrismUtils/PluginManager.py
  - Discovers, loads, unloads, and reloads app/custom plugins.
  - Handles autoload settings and monkey-patching support.

- Scripts/PrismUtils/Integration.py
  - Reads/writes integration install paths and delegates install/uninstall to app plugins.

- Scripts/PrismUtils/PathManager.py
  - Resolves project paths for scenes, renders, playblasts, products.
  - Converts between locations (global/local/custom) and extracts metadata from version folders.

See inline docstrings in these files for detailed function and class behavior.


