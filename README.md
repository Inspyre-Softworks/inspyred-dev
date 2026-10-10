# Inspyred Dev

**Capture what you notice. Turn it into work.**

Inspyred Dev is a developer observation inbox: a fast place to capture UI, UX, bug,
refactor, documentation, testing, and feature notes while you are actively using software.
The long-term goal is frictionless GitHub Projects and AI handoff without forcing you to stop
what you are doing and hunt for the corresponding source file.

## Current prototype

The first runnable shell already includes:

- A local SQLite-backed observation inbox.
- A QML/Qt Quick interface powered by Python + PySide6.
- A global capture shortcut, active-window screenshots, and system-tray operation on Windows.
- Project creation from local folders or GitHub repository links, with project-scoped inboxes.
- GitHub App device-flow sign-in with operating-system credential-vault storage.
- System, light, and dark themes.
- An explicit icon-label preference: icons only or icons + text.
- Tooltips on reusable interactive controls.
- Help metadata attached to reusable UI components.
- A clean separation between core data, services, Python/Qt bindings, and QML presentation.

## Run from source

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
inspyred-dev
```

Display command-line help or the installed version without starting the desktop UI:

```powershell
inspyred-dev --help
inspyred-dev --version
```

## Design contract

Interactive controls should carry their own user-facing contract wherever practical:

- visible label
- icon/glyph
- tooltip
- help ID / contextual help text
- accessible name
- optional keyboard shortcut

Icon-only presentation is a preference, not a requirement. Users can keep icons and display
persistent text labels alongside them.

## Planned next steps

1. GitHub repository access validation and project mapping.
2. GitHub Issues + Projects synchronization.
3. Offline sync queue and conflict handling.
4. AI-ready handoff/export.
5. Windows EXE, installer, WinGet manifest, and PyPI release automation.

## Configure GitHub sign-in

Open **Settings → GitHub** and follow the in-app setup guide. It opens GitHub's
new-app form, explains how to enable Device Flow, accepts the public client ID,
and continues directly into browser-based sign-in. The client ID is remembered
in native application settings. No client secret or private key is required.

Developers can still use ``INSPYRED_GITHUB_CLIENT_ID`` as a configuration
fallback for automated builds and local launches.

## Build the Windows bundle

```powershell
./scripts/build_windows.ps1
```

The first release workflow deliberately creates a directory-based application bundle. A signed
installer and WinGet manifest come after the capture/tray behavior is stable; the packaging boundary
is already isolated under `packaging/` so that does not require restructuring the application.

## Documentation

The Sphinx documentation lives in `docs/` and is configured for Read the Docs. Build it locally
with:

```powershell
pip install -e ".[docs]"
sphinx-build -W --keep-going -b html docs docs/_build/html
```

The application and package metadata share one version declaration: `__version__` in
`src/inspyred_dev/__init__.py`. Update that value when preparing a release.
