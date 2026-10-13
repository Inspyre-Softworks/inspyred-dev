"""Compatibility imports for the GitHub plugin controller.

New code should import these objects from :mod:`inspyred_dev.plugins.github.controller`.

Author: Taylor B. | Inspyre-Softworks.
"""

from inspyred_dev.plugins.github.controller import (
    CLIENT_ID_SETTING,
    GitHubAuthController,
    GitHubTokenStore,
    OAuthToken,
)

__all__ = [
    'CLIENT_ID_SETTING',
    'GitHubAuthController',
    'GitHubTokenStore',
    'OAuthToken',
]
