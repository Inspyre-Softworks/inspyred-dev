"""GitHub plugin lifecycle and application integration.

Author: Taylor B. | Inspyre-Softworks.
"""

from collections.abc import Callable
from pathlib import Path

from inspyred_dev import __version__
from inspyred_dev.plugins.api import (
    PluginContribution,
    PluginMetadata,
    PluginServices,
    PluginUiExtension,
)
from inspyred_dev.plugins.github.controller import GitHubAuthController


class GitHubPlugin:
    """Provide GitHub authentication, repositories, and issue publishing."""

    def __init__(
        self,
        controller_factory: Callable[[], GitHubAuthController] = GitHubAuthController,
    ) -> None:
        """Store the controller factory until application services are ready."""
        self._controller_factory = controller_factory
        self._controller: GitHubAuthController | None = None
        self._issue_linker: Callable[[int, int, str], None] | None = None

    @property
    def metadata(self) -> PluginMetadata:
        """Return the bundled plugin's stable identity."""
        return PluginMetadata('github', 'GitHub', __version__)

    def activate(self, services: PluginServices) -> PluginContribution:
        """Create GitHub's controller and connect issue results to local storage."""
        if self._controller is not None:
            raise RuntimeError('The GitHub plugin is already active.')
        self._controller = self._controller_factory()
        self._issue_linker = getattr(services.observations, 'linkGithubIssue')
        self._controller.issueCreated.connect(self._issue_linker)
        qml_root = Path(__file__).parent / 'qml'
        return PluginContribution(
            qml_context={'GitHubAuth': self._controller},
            qml_import_paths=(qml_root,),
            ui_extensions=(
                PluginUiExtension('settings.integrations', qml_root / 'GitHubSettings.qml'),
            ),
        )

    def deactivate(self) -> None:
        """Disconnect plugin-owned signal wiring."""
        if self._controller is not None and self._issue_linker is not None:
            try:
                self._controller.issueCreated.disconnect(self._issue_linker)
            except RuntimeError:
                pass
        self._controller = None
        self._issue_linker = None
