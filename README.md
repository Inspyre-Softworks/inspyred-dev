# Inspyred Dev

**Capture what you notice. Turn it into work.**

Inspyred Dev is a developer observation inbox: a fast place to capture UI, UX, bug,
refactor, documentation, testing, and feature notes while you are actively using software.
The long-term goal is frictionless GitHub Projects and AI handoff without forcing you to stop
what you are doing and hunt for the corresponding source file.

## Current prototype

The first runnable shell already includes:

- A local SQLite-backed observation inbox.
- Note shelving/restoration, priority adjustment, and confirmed permanent deletion.
- A QML/Qt Quick interface powered by Python + PySide6.
- A global capture shortcut, active-window screenshots, and system-tray operation on Windows.
- Project creation from local folders or GitHub repository links, with project-scoped inboxes.
- Project editing and automatic GitHub-remote detection for local folders.
- GitHub App device-flow sign-in with operating-system credential-vault storage.
- Repository discovery that excludes GitHub projects already added to the inbox.
- Single and batch GitHub issue creation, with persisted issue links.
- Copy-ready AI coding instructions generated from one note or a selected group.
- An in-app About window with version, ownership, license, and project links.
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

After sign-in, **Add project → GitHub repository** loads the repositories the
GitHub App can access and hides repositories that are already projects. Search
filters the picker by owner or repository name, and a manual repository URL
remains available as a fallback.

Set the GitHub App's **Issues** repository permission to **Read and write**.
Observations belonging to GitHub-backed projects then show **Create issue**;
successful creation stores and displays the resulting issue number and link.
Select several notes from one project—or use **Select all** in that project's
inbox—to create one combined AI coding instruction or a set of individual
instructions. For a GitHub-backed project, the same selection can create one
combined issue, one issue per note, or issues grouped by ordered keywords.
Every note also has its own **AI instruction** action.

Use the pencil button beside the project switcher to rename a project, update
its folder, or manually connect it to a GitHub repository. Local folder
projects are also checked shortly after startup and every five minutes; when
their ``origin`` remote points to GitHub, the existing project is upgraded in
place and keeps its notes and local folder association.
When a GitHub-backed project is active, **View on GitHub** beside **Capture**
opens its repository in the default browser.

Developers can still use ``INSPYRED_GITHUB_CLIENT_ID`` as a configuration
fallback for automated builds and local launches.

## Extend Inspyred Dev with plugins

GitHub is a bundled plugin rather than a service constructed by the application shell. Plugins
implement `ApplicationPlugin` and can contribute QObject context APIs, QML import paths, and QML
components for named UI extension slots. The settings screen currently exposes the
`settings.integrations` slot, which is also how GitHub adds its settings card.

Third-party packages register a plugin object or no-argument plugin class with a Python entry point:

```toml
[project.entry-points."inspyred_dev.plugins"]
my-integration = "my_package.plugin:MyPlugin"
```

The About window provides a read-only list of bundled, package-provided, and user-installed plugins
and whether each is enabled. Open **Settings → Plugins → Manage plugins** to install a local ZIP or
download one from an HTTPS GitHub repository, branch, or archive URL. User plugins can be enabled,
disabled, and uninstalled in the Plugin Manager; changes to active plugins take effect after restart.

An installable ZIP contains exactly one `inspyred-plugin.json` manifest, optionally below a single
GitHub archive root directory:

```json
{
  "id": "example-plugin",
  "name": "Example Plugin",
  "version": "1.0.0",
  "entry_point": "plugin:Plugin"
}
```

The entry point must refer to a top-level Python module or package shipped beside the manifest.
Remote downloads are restricted to GitHub, and archives are size-limited and checked for unsafe
paths before extraction. Plugins execute Python code with the user's permissions, so only trusted
plugins should be installed.

The public contracts live in `inspyred_dev.plugins`. Each plugin ID and QML context-property name
must be unique. Plugin-owned resources remain alive until the application shuts down, when plugins
are deactivated in reverse activation order.

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
