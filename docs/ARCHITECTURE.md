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

The provider boundary is intentional. GitHub Issues + Projects are the first remote backend, not a
permanent assumption embedded into every model and screen.

Local SQLite is authoritative for initial capture. Remote synchronization is a later operation so
capture remains instant and resilient.
