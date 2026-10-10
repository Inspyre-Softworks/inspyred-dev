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

GitHub authentication
---------------------

Inspyred Dev uses GitHub App device flow for desktop sign-in. Open
**Settings → GitHub** and follow the setup guide to create a GitHub App, enable
Device Flow, and save its public client ID. The application then starts sign-in,
displays the temporary device code, and opens GitHub's verification page in the
default browser. ``INSPYRED_GITHUB_CLIENT_ID`` remains available as a fallback
for development and automated builds.

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
