"""Context-sensitive help registry.

Author: Taylor B. | Inspyre-Softworks.
"""

from PySide6.QtCore import QObject, Slot


class HelpRegistry(QObject):
    """Keep contextual help attached to semantic control IDs."""

    _help = {
        'capture-observation': (
            'Capture a new developer observation. The observation is saved locally first so '
            'capture does not depend on GitHub or network availability.'
        ),
        'appearance-theme': 'Choose whether Inspyred Dev follows the system, light, or dark theme.',
        'appearance-labels': (
            'Choose whether navigation and action controls show icons only or icons with '
            'persistent text labels. Tooltips remain available in either mode.'
        ),
        'inbox': 'Shows newly captured observations that have not been triaged yet.',
        'project-switcher': (
            'Choose which project inbox to display. New observations are saved to the selected '
            'project; captures made from All projects go to Inspyred Dev.'
        ),
        'add-project': (
            'Create a project from an existing local folder or a GitHub repository link, then '
            'switch directly to its inbox.'
        ),
        'github-sign-in': (
            'Sign in through GitHub using a short-lived device code. Access and refresh tokens '
            'are stored in the operating system credential vault.'
        ),
    }

    @Slot(str, result=str)
    def textFor(self, help_id: str) -> str:  # noqa: N802
        """Return contextual help for a semantic control identifier.

        Parameters
        ----------
        help_id : str
            Stable identifier attached to a QML control.

        Returns
        -------
        str
            The help text, or an empty string when the identifier is unknown.
        """
        return self._help.get(help_id, '')
