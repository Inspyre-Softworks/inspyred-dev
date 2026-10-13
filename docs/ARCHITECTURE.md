# Inspyred Dev Architecture

Author: **Taylor B. | Inspyre-Softworks.**

```text
                        ┌─────────────────────┐
                        │ Qt Quick / QML UI   │
                        └──────────┬──────────┘
                                   │
                      Qt-facing models/services
                                   │
               ┌───────────────────┴───────────────────┐
               │                                       │
        Core domain models                       Capture services
               │                                       │
      ┌────────┼────────┐                     window / screenshot /
      │        │        │                       hotkey context
   SQLite   Providers   AI handoff
              │
        GitHub first
```

The plugin boundary is intentional. The application shell owns local models and services, then
activates bundled plugins plus packages published in the ``inspyred_dev.plugins`` Python entry-point
group. Plugins receive a narrow set of application services and may contribute QML context objects,
QML import paths, and QML components for named application UI slots.

GitHub uses the same public contract available to future plugins. It owns its controller,
issue-result signal wiring, and settings card; the card is loaded through the
``settings.integrations`` slot instead of being constructed by the application bootstrap. Plugin
IDs and contributed QML context names must be unique. Plugins are deactivated in reverse activation
order during shutdown.

Third-party plugin entry points resolve to either an object implementing ``ApplicationPlugin`` or a
plugin class with a no-argument constructor. A UI component may declare a ``host`` property when it
needs to communicate with the screen containing its extension slot.

The registry also owns the installed-plugin catalog. About presents that catalog read-only; a
dedicated Plugin Manager opened from Settings owns installation, enable/disable, and removal
controls. Manifest-based ZIP plugins live in the platform user-data directory, while enabled state
and pending removals are stored in native application settings. GitHub downloads and archive
validation run away from the UI thread. Changes to active plugin code are deliberately applied at
the next process start rather than attempting to unload Python and QML objects from a live Qt tree.

Local SQLite is authoritative for initial capture. Remote synchronization is a later operation so
capture remains instant and resilient.
