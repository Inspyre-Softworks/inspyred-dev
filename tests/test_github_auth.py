"""Tests for GitHub authentication credentials and expiration behavior."""

import json

import keyring
from PySide6.QtCore import QSettings

from inspyred_dev.gui.github_auth import CLIENT_ID_SETTING, GitHubAuthController, GitHubTokenStore, OAuthToken


def test_oauth_token_tracks_access_and_refresh_expiration() -> None:
    """Convert relative GitHub expirations into durable timestamps."""
    token = OAuthToken.from_payload(
        {
            'access_token': 'access',
            'refresh_token': 'refresh',
            'expires_in': 3600,
            'refresh_token_expires_in': 7200,
        },
        now=1000,
    )

    assert token.access_is_current(now=1200)
    assert not token.access_is_current(now=4550)
    assert token.can_refresh(now=4550)
    assert not token.can_refresh(now=8150)


def test_token_store_uses_credential_vault(monkeypatch) -> None:
    """Round-trip token material without writing it to application settings."""
    vault: dict[tuple[str, str], str] = {}

    monkeypatch.setattr(
        keyring,
        'set_password',
        lambda service, account, value: vault.__setitem__((service, account), value),
    )
    monkeypatch.setattr(
        keyring,
        'get_password',
        lambda service, account: vault.get((service, account)),
    )
    monkeypatch.setattr(
        keyring,
        'delete_password',
        lambda service, account: vault.pop((service, account), None),
    )
    store = GitHubTokenStore()
    token = OAuthToken('access', 'refresh', 1234, 5678)

    assert store.save(token)
    stored_payload = json.loads(next(iter(vault.values())))
    assert stored_payload['access_token'] == 'access'
    assert store.load() == token

    store.clear()
    assert store.load() is None


def test_controller_loads_client_id_from_native_settings(tmp_path, monkeypatch) -> None:
    """Allow GitHub setup to be completed and restored entirely through the GUI."""
    monkeypatch.delenv('INSPYRED_GITHUB_CLIENT_ID', raising=False)
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    settings.setValue(CLIENT_ID_SETTING, 'Iv1abcdef0123456789')

    controller = GitHubAuthController(settings=settings)

    assert controller.configured
    assert controller.clientId == 'Iv1abcdef0123456789'


def test_invalid_gui_client_id_is_not_saved(tmp_path, monkeypatch) -> None:
    """Reject obvious copy/paste mistakes before making an OAuth request."""
    monkeypatch.delenv('INSPYRED_GITHUB_CLIENT_ID', raising=False)
    settings = QSettings(str(tmp_path / 'settings.ini'), QSettings.Format.IniFormat)
    controller = GitHubAuthController(settings=settings)

    controller.configureAndSignIn('not a client id')

    assert not controller.configured
    assert settings.value(CLIENT_ID_SETTING) is None
    assert 'Client ID' in controller.errorMessage


def test_repository_options_exclude_existing_projects() -> None:
    """Only offer valid GitHub repositories that are not already projects."""
    payload = [
        {
            'full_name': 'Inspyre-Softworks/inspyred-dev',
            'html_url': 'https://github.com/Inspyre-Softworks/inspyred-dev',
            'id': 12345678901,
            'default_branch': 'main',
        },
        {
            'full_name': 'Inspyre-Softworks/website',
            'html_url': 'https://github.com/Inspyre-Softworks/website',
        },
        {'full_name': '', 'html_url': 'https://github.com/broken/repository'},
    ]

    repositories = GitHubAuthController._repository_options(
        payload,
        {'https://github.com/inspyre-softworks/website'},
    )

    assert repositories == [
        {
            'full_name': 'Inspyre-Softworks/inspyred-dev',
            'url': 'https://github.com/Inspyre-Softworks/inspyred-dev',
            'id': 12345678901,
            'default_branch': 'main',
        }
    ]


def test_issue_body_contains_observation_context() -> None:
    """Format captured context and triage metadata as GitHub Markdown."""
    body = GitHubAuthController.format_issue_body(
        'The dialog clips on small screens.',
        'Bug',
        'P1',
        'Add project',
    )

    assert body.startswith('The dialog clips on small screens.')
    assert '- **Type:** Bug' in body
    assert '- **Priority:** P1' in body
    assert '- **Area:** Add project' in body


def test_create_issue_targets_project_repository(monkeypatch) -> None:
    """Send the observation to the selected project's issue endpoint."""
    controller = GitHubAuthController(client_id='Iv1abcdef0123456789')
    controller._status = 'signed_in'
    controller._token = OAuthToken('access-token')
    request: dict[str, object] = {}

    def capture(url, payload, callback) -> None:
        request.update(url=url, payload=payload, callback=callback)

    monkeypatch.setattr(controller, '_authenticated_post_json', capture)

    controller.createIssue(
        17,
        'https://github.com/Inspyre-Softworks/inspyred-dev',
        'Create GitHub issue',
        'Publish the observation.',
        'Feature',
        'P2',
        'Inbox',
    )

    assert request['url'] == (
        'https://api.github.com/repos/Inspyre-Softworks/inspyred-dev/issues'
    )
    assert request['payload'] == {
        'title': 'Create GitHub issue',
        'body': GitHubAuthController.format_issue_body(
            'Publish the observation.', 'Feature', 'P2', 'Inbox'
        ),
    }
    assert controller.issueCreationObservationId == 17
