Getting started
===============

Inspyred Dev requires Python 3.13 or newer.

Installation
------------

Create and activate a virtual environment, then install the project in editable
mode:

.. code-block:: powershell

   py -3.13 -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -e .

Run the application with:

.. code-block:: powershell

   inspyred-dev

On Windows, press ``Ctrl+Shift+N`` from any application to open quick capture.
Closing the inbox keeps Inspyred Dev available in the system tray. Use the tray
menu to reopen the inbox, start quick capture, or quit the application.

Use the project switcher in the lower-right corner to change inboxes. Its add
button creates a project from an existing local folder or an HTTPS GitHub
repository link. A custom display name is optional.

The pencil button edits the active project. Use it to rename a project, change
its folder, or manually connect an existing inbox to a GitHub repository. Notes
remain attached when a project is renamed or upgraded. Inspyred Dev checks
local folder projects shortly after startup and every five minutes; if a
folder's Git ``origin`` becomes a GitHub HTTPS or SSH remote, the existing
project is automatically upgraded to a GitHub-backed project.

GitHub authentication
---------------------

Inspyred Dev uses GitHub App device flow for desktop sign-in. Open
**Settings → GitHub** and follow the setup guide to create a GitHub App, enable
Device Flow, and save its public client ID. The application then starts sign-in,
displays the temporary device code, and opens GitHub's verification page in the
default browser. ``INSPYRED_GITHUB_CLIENT_ID`` remains available as a fallback
for development and automated builds.

When adding a GitHub-backed project, the project dialog lists repositories
available to the authenticated GitHub App and excludes repositories already
present in the project catalog. The GitHub App must be installed with access to
the relevant repositories and read access to repository metadata. Search the
list by owner or repository name. A manual URL field remains available when a
repository is not returned by the API.

To publish observations as issues, set the GitHub App's **Issues** repository
permission to **Read and write** and approve that access for its installation.
Each observation in a GitHub-backed project then provides **Create issue**.
Inspyred Dev sends its title, context, type, priority, and area to GitHub and
stores the returned issue number and URL in the local observation database.

Use the selection control on several observations from one project, or use
**Select all** in that project's inbox, to create a batch. Selection and AI
instructions remain available for local projects. For a GitHub-backed project,
unlinked selected notes can become one combined issue, one issue per note, or
several issues grouped by comma-separated keywords. Keyword matching is
case-insensitive, uses the first matching keyword, and preserves unmatched
notes in an ``Other`` issue. A batch never spans projects.

AI coding instructions
----------------------

Every observation provides an **AI instruction** action that creates a
copy-ready coding brief with its objective, context, classification, repository,
and delivery requirements. For a selected group, choose one combined instruction
or separate instructions and copy the result after reviewing it. Instruction
generation is local and does not send the observation to an AI service.

Access and refresh tokens are stored through the operating system credential
vault rather than in the application database or settings. A client secret and
GitHub App private key are not stored in the desktop application.

Command-line options
--------------------

Display command-line help or the installed version without opening the desktop
interface:

.. code-block:: powershell

   inspyred-dev --help
   inspyred-dev --version

The short forms ``-h`` and ``-v`` are also supported.

Documentation
-------------

Install the documentation dependencies and build the HTML site locally:

.. code-block:: powershell

   pip install -e ".[docs]"
   sphinx-build -W --keep-going -b html docs docs/_build/html
