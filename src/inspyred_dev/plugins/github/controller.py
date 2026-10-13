"""GitHub device-flow authentication provided by the GitHub plugin.

Author: Taylor B. | Inspyre-Softworks.
"""

from dataclasses import asdict, dataclass
import json
import os
import time
from urllib.parse import quote, urlencode, urlparse

import keyring
from keyring.errors import KeyringError
from PySide6.QtCore import QByteArray, QObject, QSettings, QTimer, QUrl, Signal, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtCore import Property


DEVICE_CODE_URL = 'https://github.com/login/device/code'
ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'
AUTHENTICATED_USER_URL = 'https://api.github.com/user'
AUTHENTICATED_REPOSITORIES_URL = 'https://api.github.com/user/repos'
GITHUB_API_VERSION = '2026-03-10'
DEVICE_GRANT = 'urn:ietf:params:oauth:grant-type:device_code'
KEYRING_SERVICE = 'Inspyred Dev GitHub'
KEYRING_ACCOUNT = 'user-access-token'
CLIENT_ID_SETTING = 'github/clientId'
GITHUB_APP_CREATION_URL = 'https://github.com/settings/apps/new'
GITHUB_APP_SETTINGS_URL = 'https://github.com/settings/apps'


@dataclass(frozen=True)
class OAuthToken:
    """Stored GitHub user access and refresh credentials."""

    access_token: str
    refresh_token: str = ''
    expires_at: float = 0
    refresh_expires_at: float = 0

    @classmethod
    def from_payload(cls, payload: dict[str, object], now: float | None = None) -> 'OAuthToken':
        """Build expiration timestamps from a GitHub token response."""
        issued_at = time.time() if now is None else now
        expires_in = int(payload.get('expires_in', 0) or 0)
        refresh_expires_in = int(payload.get('refresh_token_expires_in', 0) or 0)
        return cls(
            access_token=str(payload.get('access_token', '')),
            refresh_token=str(payload.get('refresh_token', '')),
            expires_at=issued_at + expires_in if expires_in else 0,
            refresh_expires_at=issued_at + refresh_expires_in if refresh_expires_in else 0,
        )

    def access_is_current(self, now: float | None = None) -> bool:
        """Return whether the access token can be used without refreshing."""
        current_time = time.time() if now is None else now
        return bool(
            self.access_token and (not self.expires_at or self.expires_at > current_time + 60)
        )

    def can_refresh(self, now: float | None = None) -> bool:
        """Return whether the refresh token is still usable."""
        current_time = time.time() if now is None else now
        return bool(
            self.refresh_token
            and (not self.refresh_expires_at or self.refresh_expires_at > current_time + 60)
        )


class GitHubTokenStore:
    """Store GitHub credentials in the operating system credential vault."""

    def load(self) -> OAuthToken | None:
        """Load a stored token, returning ``None`` when unavailable."""
        try:
            value = keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
        except KeyringError:
            return None
        if not value:
            return None
        try:
            payload = json.loads(value)
            return OAuthToken(
                access_token=str(payload['access_token']),
                refresh_token=str(payload.get('refresh_token', '')),
                expires_at=float(payload.get('expires_at', 0)),
                refresh_expires_at=float(payload.get('refresh_expires_at', 0)),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return None

    def save(self, token: OAuthToken) -> bool:
        """Persist a token securely when a credential backend is available."""
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, json.dumps(asdict(token)))
        except KeyringError:
            return False
        return True

    def clear(self) -> None:
        """Remove stored credentials if they exist."""
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
        except (KeyringError, keyring.errors.PasswordDeleteError):
            pass


class GitHubAuthController(QObject):
    """Run GitHub's OAuth device flow without blocking the Qt event loop."""

    stateChanged = Signal()
    repositoriesChanged = Signal()
    issueCreated = Signal(int, int, str)

    def __init__(
        self,
        client_id: str | None = None,
        token_store: GitHubTokenStore | None = None,
        network: QNetworkAccessManager | None = None,
        settings: QSettings | None = None,
    ) -> None:
        """Restore credentials and prepare asynchronous GitHub authentication."""
        super().__init__()
        self._settings = settings or QSettings('Inspyre-Softworks', 'Inspyred Dev')
        saved_client_id = str(self._settings.value(CLIENT_ID_SETTING, '') or '')
        self._client_id = (
            client_id or saved_client_id or os.environ.get('INSPYRED_GITHUB_CLIENT_ID', '')
        ).strip()
        self._token_store = token_store or GitHubTokenStore()
        self._network = network or QNetworkAccessManager(self)
        self._poll_timer = QTimer(self)
        self._poll_timer.setSingleShot(True)
        self._poll_timer.timeout.connect(self._poll_token)

        self._status = 'idle' if self._client_id else 'not_configured'
        self._error_message = ''
        self._device_code = ''
        self._user_code = ''
        self._verification_uri = ''
        self._poll_interval_seconds = 5
        self._login = ''
        self._display_name = ''
        self._avatar_url = ''
        self._repositories: list[dict[str, object]] = []
        self._repositories_loading = False
        self._repositories_error = ''
        self._repository_exclusions: set[str] = set()
        self._issue_creation_observation_id = 0
        self._issue_creation_error_observation_id = 0
        self._issue_creation_error = ''
        self._issue_queue: list[dict[str, object]] = []
        self._active_issue_observation_ids: list[int] = []
        self._issue_batch_total = 0
        self._issue_batch_completed = 0
        self._token = self._token_store.load()

        if self._client_id and self._token is not None:
            QTimer.singleShot(0, self._restore_session)

    @Property(bool, notify=stateChanged)
    def configured(self) -> bool:
        """Return whether a GitHub App client ID is configured."""
        return bool(self._client_id)

    @Property(str, notify=stateChanged)
    def clientId(self) -> str:  # noqa: N802
        """Return the configured public GitHub App client ID."""
        return self._client_id

    @Property(bool, notify=stateChanged)
    def signedIn(self) -> bool:  # noqa: N802
        """Return whether a GitHub identity has been validated."""
        return self._status == 'signed_in'

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        """Return whether authentication work is in progress."""
        return self._status in {
            'requesting_code',
            'waiting_for_authorization',
            'checking_account',
            'refreshing',
        }

    @Property(str, notify=stateChanged)
    def status(self) -> str:
        """Return the current authentication state identifier."""
        return self._status

    @Property(str, notify=stateChanged)
    def errorMessage(self) -> str:  # noqa: N802
        """Return a user-facing authentication error."""
        return self._error_message

    @Property(str, notify=stateChanged)
    def userCode(self) -> str:  # noqa: N802
        """Return the short code entered on GitHub's device page."""
        return self._user_code

    @Property(str, notify=stateChanged)
    def verificationUri(self) -> str:  # noqa: N802
        """Return GitHub's device verification URL."""
        return self._verification_uri

    @Property(str, notify=stateChanged)
    def login(self) -> str:
        """Return the authenticated GitHub login."""
        return self._login

    @Property(str, notify=stateChanged)
    def displayName(self) -> str:  # noqa: N802
        """Return the authenticated user's display name."""
        return self._display_name

    @Property(str, notify=stateChanged)
    def avatarUrl(self) -> str:  # noqa: N802
        """Return the authenticated user's avatar URL."""
        return self._avatar_url

    @Property('QStringList', notify=repositoriesChanged)
    def repositoryNames(self) -> list[str]:  # noqa: N802
        """Return display names for repositories that can still be added."""
        return [str(repository['full_name']) for repository in self._repositories]

    @Property(bool, notify=repositoriesChanged)
    def repositoriesLoading(self) -> bool:  # noqa: N802
        """Return whether accessible repositories are being fetched."""
        return self._repositories_loading

    @Property(str, notify=repositoriesChanged)
    def repositoriesError(self) -> str:  # noqa: N802
        """Return a user-facing repository loading error."""
        return self._repositories_error

    @Property(int, notify=stateChanged)
    def issueCreationObservationId(self) -> int:  # noqa: N802
        """Return the observation currently being published to GitHub."""
        return self._issue_creation_observation_id

    @Property(int, notify=stateChanged)
    def issueCreationErrorObservationId(self) -> int:  # noqa: N802
        """Return the observation associated with the latest issue error."""
        return self._issue_creation_error_observation_id

    @Property(str, notify=stateChanged)
    def issueCreationError(self) -> str:  # noqa: N802
        """Return the latest user-facing GitHub issue creation error."""
        return self._issue_creation_error

    @Property(int, notify=stateChanged)
    def issueBatchTotal(self) -> int:  # noqa: N802
        """Return the number of GitHub issues in the active batch."""
        return self._issue_batch_total

    @Property(int, notify=stateChanged)
    def issueBatchCompleted(self) -> int:  # noqa: N802
        """Return the number of GitHub issues completed in the active batch."""
        return self._issue_batch_completed

    def _set_state(self, status: str, error: str = '') -> None:
        self._status = status
        self._error_message = error
        self.stateChanged.emit()

    @staticmethod
    def _json(reply: QNetworkReply) -> dict[str, object]:
        try:
            value = json.loads(bytes(reply.readAll()).decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def _post_form(self, url: str, fields: dict[str, str], callback) -> None:
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'Accept', b'application/json')
        request.setRawHeader(b'Content-Type', b'application/x-www-form-urlencoded')
        request.setRawHeader(b'User-Agent', b'Inspyred-Dev')
        reply = self._network.post(request, QByteArray(urlencode(fields).encode('utf-8')))
        reply.finished.connect(lambda: self._finish_reply(reply, callback))

    def _authenticated_get(self, url: str, callback) -> None:
        if self._token is None:
            return
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'Accept', b'application/vnd.github+json')
        request.setRawHeader(b'Authorization', f'Bearer {self._token.access_token}'.encode('ascii'))
        request.setRawHeader(b'User-Agent', b'Inspyred-Dev')
        request.setRawHeader(b'X-GitHub-Api-Version', GITHUB_API_VERSION.encode('ascii'))
        reply = self._network.get(request)
        reply.finished.connect(lambda: self._finish_reply(reply, callback))

    def _authenticated_post_json(self, url: str, payload: dict[str, object], callback) -> None:
        if self._token is None:
            return
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'Accept', b'application/vnd.github+json')
        request.setRawHeader(b'Content-Type', b'application/json')
        request.setRawHeader(b'Authorization', f'Bearer {self._token.access_token}'.encode('ascii'))
        request.setRawHeader(b'User-Agent', b'Inspyred-Dev')
        request.setRawHeader(b'X-GitHub-Api-Version', GITHUB_API_VERSION.encode('ascii'))
        reply = self._network.post(request, QByteArray(json.dumps(payload).encode('utf-8')))
        reply.finished.connect(lambda: self._finish_reply(reply, callback))

    @staticmethod
    def _finish_reply(reply: QNetworkReply, callback) -> None:
        try:
            callback(reply)
        finally:
            reply.deleteLater()

    def _restore_session(self) -> None:
        if self._token is None:
            return
        if self._token.access_is_current():
            self._load_user()
        elif self._token.can_refresh():
            self._refresh_token()
        else:
            self._clear_session()

    @staticmethod
    def _valid_client_id(value: str) -> bool:
        """Return whether a value is plausible as a public GitHub client ID."""
        return len(value) >= 10 and value.isascii() and value.isalnum()

    @Slot(str)
    def configureAndSignIn(self, client_id: str) -> None:  # noqa: N802
        """Save a public client ID from the GUI and immediately start sign-in."""
        value = client_id.strip()
        if not self._valid_client_id(value):
            self._set_state(
                'not_configured',
                'Enter the public Client ID shown on the GitHub App settings page.',
            )
            return
        if value != self._client_id:
            self._clear_session()
            self._client_id = value
            self._settings.setValue(CLIENT_ID_SETTING, value)
            self._settings.sync()
        elif not self._settings.value(CLIENT_ID_SETTING, ''):
            self._settings.setValue(CLIENT_ID_SETTING, value)
            self._settings.sync()
        self.signIn()

    @Slot()
    def openGitHubAppCreation(self) -> None:  # noqa: N802
        """Open GitHub's new-app form used by the in-app setup guide."""
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl(GITHUB_APP_CREATION_URL))

    @Slot()
    def openGitHubAppSettings(self) -> None:  # noqa: N802
        """Open the owner's GitHub Apps page to manage repository access."""
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl(GITHUB_APP_SETTINGS_URL))

    @Slot('QStringList')
    def loadRepositories(self, excluded_urls: list[str]) -> None:  # noqa: N802
        """Fetch accessible repositories, excluding projects already added."""
        self._repositories = []
        self._repositories_error = ''
        self._repository_exclusions = {url.rstrip('/').casefold() for url in excluded_urls}
        if not self.signedIn or self._token is None:
            self._repositories_loading = False
            self._repositories_error = 'Sign in with GitHub in Settings to browse repositories.'
            self.repositoriesChanged.emit()
            return
        self._repositories_loading = True
        self.repositoriesChanged.emit()
        self._load_repository_page(1)

    def _load_repository_page(self, page: int) -> None:
        url = f'{AUTHENTICATED_REPOSITORIES_URL}?per_page=100&sort=updated&page={page}'
        self._authenticated_get(url, lambda reply: self._handle_repository_page(reply, page))

    @staticmethod
    def _repository_options(
        payload: object,
        excluded_urls: set[str],
    ) -> list[dict[str, object]]:
        """Normalize repository API records and remove existing project URLs."""
        if not isinstance(payload, list):
            return []
        repositories: list[dict[str, object]] = []
        for value in payload:
            if not isinstance(value, dict):
                continue
            full_name = str(value.get('full_name', '')).strip()
            html_url = str(value.get('html_url', '')).strip().rstrip('/')
            if (
                not full_name
                or not html_url
                or html_url.casefold() in excluded_urls
                or any(str(item['url']).casefold() == html_url.casefold() for item in repositories)
            ):
                continue
            repositories.append(
                {
                    'full_name': full_name,
                    'url': html_url,
                    'id': int(value.get('id', 0) or 0),
                    'default_branch': str(value.get('default_branch', '')).strip(),
                }
            )
        return repositories

    def _handle_repository_page(self, reply: QNetworkReply, page: int) -> None:
        status_code = int(reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 0)
        try:
            payload: object = json.loads(bytes(reply.readAll()).decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            payload = None
        if reply.error() != QNetworkReply.NetworkError.NoError or status_code != 200:
            self._repositories_loading = False
            self._repositories_error = (
                'GitHub could not load repositories. Confirm the app is installed and has '
                'read access to repository metadata.'
            )
            self.repositoriesChanged.emit()
            return
        page_repositories = self._repository_options(payload, self._repository_exclusions)
        known_urls = {str(repository['url']).casefold() for repository in self._repositories}
        self._repositories.extend(
            repository
            for repository in page_repositories
            if str(repository['url']).casefold() not in known_urls
        )
        if isinstance(payload, list) and len(payload) == 100:
            self._load_repository_page(page + 1)
            return
        self._repositories_loading = False
        self.repositoriesChanged.emit()

    @Slot(int, result=str)
    def repositoryUrlAt(self, index: int) -> str:  # noqa: N802
        """Return the canonical URL for a repository selection."""
        if 0 <= index < len(self._repositories):
            return str(self._repositories[index]['url'])
        return ''

    @Slot(int, result=str)
    def repositoryIdAt(self, index: int) -> str:  # noqa: N802
        """Return the stable GitHub ID for a repository selection."""
        if 0 <= index < len(self._repositories):
            return str(self._repositories[index]['id'])
        return '0'

    @Slot(int, result=str)
    def repositoryDefaultBranchAt(self, index: int) -> str:  # noqa: N802
        """Return the default branch for a repository selection."""
        if 0 <= index < len(self._repositories):
            return str(self._repositories[index]['default_branch'])
        return ''

    @staticmethod
    def format_issue_body(details: str, kind: str, priority: str, area: str) -> str:
        """Build a readable GitHub issue body from an observation."""
        context = details.strip() or '_No additional context was captured._'
        area_value = area.strip() or 'Not specified'
        return (
            f'{context}\n\n'
            '---\n'
            'Created from an Inspyred Dev observation.\n\n'
            f'- **Type:** {kind}\n'
            f'- **Priority:** {priority}\n'
            f'- **Area:** {area_value}'
        )

    @Slot(int, str, str, str, str, str, str)
    def createIssue(  # noqa: N802
        self,
        observation_id: int,
        repository_url: str,
        title: str,
        details: str,
        kind: str,
        priority: str,
        area: str,
    ) -> None:
        """Create a GitHub issue from a local observation."""
        self._begin_issue_batch(
            [
                {
                    'observation_ids': [observation_id],
                    'repository_url': repository_url,
                    'title': title.strip(),
                    'body': self.format_issue_body(details, kind, priority, area),
                }
            ]
        )

    @staticmethod
    def _issue_endpoint(repository_url: str) -> str:
        parsed = urlparse(repository_url.strip())
        parts = [part for part in parsed.path.split('/') if part]
        if parsed.hostname != 'github.com' or len(parts) != 2:
            return ''
        owner, repository = parts
        repository = repository.removesuffix('.git')
        return (
            f'https://api.github.com/repos/{quote(owner, safe="")}/'
            f'{quote(repository, safe="")}/issues'
        )

    @Slot('QVariantList')
    def createIssueBatch(self, requests: list[object]) -> None:  # noqa: N802
        """Create one or more issues for a repository-scoped note selection."""
        normalized: list[dict[str, object]] = []
        repository_urls: set[str] = set()
        for value in requests:
            if not isinstance(value, dict):
                continue
            observation_ids: list[int] = []
            raw_observation_ids = value.get('observation_ids', [])
            if isinstance(raw_observation_ids, list):
                for raw_observation_id in raw_observation_ids:
                    try:
                        observation_id = int(raw_observation_id)
                    except (TypeError, ValueError):
                        continue
                    if observation_id > 0:
                        observation_ids.append(observation_id)
            repository_url = str(value.get('repository_url', '')).strip()
            title = str(value.get('title', '')).strip()
            body = str(value.get('body', '')).strip()
            if not observation_ids or not self._issue_endpoint(repository_url) or not title:
                continue
            repository_urls.add(repository_url.rstrip('/').casefold())
            normalized.append(
                {
                    'observation_ids': observation_ids,
                    'repository_url': repository_url,
                    'title': title,
                    'body': body,
                }
            )
        if len(repository_urls) > 1:
            observation_id = int(normalized[0]['observation_ids'][0]) if normalized else 0
            self._set_issue_error(observation_id, 'A batch must target one GitHub repository.')
            return
        self._begin_issue_batch(normalized)

    def _begin_issue_batch(self, requests: list[dict[str, object]]) -> None:
        observation_id = int(requests[0]['observation_ids'][0]) if requests else 0
        if not self.signedIn or self._token is None:
            self._set_issue_error(observation_id, 'Sign in with GitHub before creating issues.')
            return
        if self._issue_creation_observation_id:
            return
        if not requests:
            self._set_issue_error(observation_id, 'Select at least one valid observation.')
            return
        if (
            len({str(request['repository_url']).rstrip('/').casefold() for request in requests})
            != 1
        ):
            self._set_issue_error(observation_id, 'A batch must target one GitHub repository.')
            return
        self._issue_creation_error_observation_id = 0
        self._issue_creation_error = ''
        self._issue_queue = list(requests)
        self._active_issue_observation_ids = []
        self._issue_batch_total = len(requests)
        self._issue_batch_completed = 0
        self._start_next_issue()

    def _start_next_issue(self) -> None:
        if not self._issue_queue:
            self._issue_creation_observation_id = 0
            self._active_issue_observation_ids = []
            self.stateChanged.emit()
            return
        request = self._issue_queue.pop(0)
        observation_ids = [int(value) for value in request['observation_ids']]
        self._active_issue_observation_ids = observation_ids
        self._issue_creation_observation_id = observation_ids[0]
        self.stateChanged.emit()
        endpoint = self._issue_endpoint(str(request['repository_url']))
        self._authenticated_post_json(
            endpoint,
            {
                'title': str(request['title']),
                'body': str(request['body']),
            },
            self._handle_issue_created,
        )

    def _set_issue_error(self, observation_id: int, message: str) -> None:
        self._issue_creation_observation_id = 0
        self._active_issue_observation_ids = []
        self._issue_queue = []
        self._issue_creation_error_observation_id = observation_id
        self._issue_creation_error = message
        self.stateChanged.emit()

    def _handle_issue_created(self, reply: QNetworkReply) -> None:
        observation_ids = list(self._active_issue_observation_ids)
        observation_id = observation_ids[0] if observation_ids else 0
        payload = self._json(reply)
        status_code = int(reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 0)
        if reply.error() != QNetworkReply.NetworkError.NoError or status_code != 201:
            messages = {
                403: 'GitHub denied issue creation. Give the app Issues: write permission.',
                404: 'GitHub could not access this repository. Check the app installation.',
                410: 'Issues are disabled for this repository.',
                422: 'GitHub rejected the issue. Check its title and try again.',
            }
            api_message = str(payload.get('message', '')).strip()
            self._set_issue_error(
                observation_id,
                messages.get(status_code, api_message or reply.errorString()),
            )
            return
        issue_number = int(payload.get('number', 0) or 0)
        issue_url = str(payload.get('html_url', '')).strip()
        if not issue_number or not issue_url:
            self._set_issue_error(observation_id, 'GitHub returned an incomplete issue response.')
            return
        self._issue_creation_observation_id = 0
        self._issue_creation_error_observation_id = 0
        self._issue_creation_error = ''
        self._active_issue_observation_ids = []
        for linked_observation_id in observation_ids:
            self.issueCreated.emit(linked_observation_id, issue_number, issue_url)
        self._issue_batch_completed += 1
        self._start_next_issue()

    @Slot()
    def signIn(self) -> None:  # noqa: N802
        """Start GitHub's browser-assisted device authorization flow."""
        if not self._client_id:
            self._set_state(
                'not_configured',
                'Complete GitHub setup below before signing in.',
            )
            return
        self._poll_timer.stop()
        self._device_code = ''
        self._user_code = ''
        self._verification_uri = ''
        self._set_state('requesting_code')
        self._post_form(
            DEVICE_CODE_URL,
            {'client_id': self._client_id},
            self._handle_device_code,
        )

    def _handle_device_code(self, reply: QNetworkReply) -> None:
        payload = self._json(reply)
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._set_state('error', reply.errorString())
            return
        self._device_code = str(payload.get('device_code', ''))
        self._user_code = str(payload.get('user_code', ''))
        self._verification_uri = str(payload.get('verification_uri', ''))
        self._poll_interval_seconds = max(5, int(payload.get('interval', 5) or 5))
        if not self._device_code or not self._user_code or not self._verification_uri:
            self._set_state('error', 'GitHub returned an incomplete device authorization response.')
            return
        self._set_state('waiting_for_authorization')
        self.openVerificationPage()
        self._poll_timer.start(self._poll_interval_seconds * 1000)

    def _poll_token(self) -> None:
        if self._status != 'waiting_for_authorization' or not self._device_code:
            return
        self._post_form(
            ACCESS_TOKEN_URL,
            {
                'client_id': self._client_id,
                'device_code': self._device_code,
                'grant_type': DEVICE_GRANT,
            },
            self._handle_token_poll,
        )

    def _handle_token_poll(self, reply: QNetworkReply) -> None:
        payload = self._json(reply)
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._set_state('error', reply.errorString())
            return
        error = str(payload.get('error', ''))
        if error == 'authorization_pending':
            self._poll_timer.start(self._poll_interval_seconds * 1000)
            return
        if error == 'slow_down':
            self._poll_interval_seconds += 5
            self._poll_timer.start(self._poll_interval_seconds * 1000)
            return
        if error:
            messages = {
                'expired_token': 'The GitHub sign-in code expired. Start sign-in again.',
                'access_denied': 'GitHub sign-in was cancelled.',
                'device_flow_disabled': 'Device flow is not enabled for the Inspyred GitHub App.',
                'incorrect_client_credentials': 'The configured GitHub App client ID is invalid.',
            }
            self._set_state(
                'error', messages.get(error, str(payload.get('error_description', error)))
            )
            return
        self._accept_token(payload)

    def _accept_token(self, payload: dict[str, object]) -> None:
        token = OAuthToken.from_payload(payload)
        if not token.access_token:
            self._set_state('error', 'GitHub did not return an access token.')
            return
        if not self._token_store.save(token):
            self._set_state('error', 'GitHub credentials could not be stored securely.')
            return
        self._token = token
        self._device_code = ''
        self._user_code = ''
        self._verification_uri = ''
        self._load_user()

    def _refresh_token(self) -> None:
        if self._token is None or not self._token.can_refresh():
            self._clear_session()
            return
        self._set_state('refreshing')
        self._post_form(
            ACCESS_TOKEN_URL,
            {
                'client_id': self._client_id,
                'grant_type': 'refresh_token',
                'refresh_token': self._token.refresh_token,
            },
            self._handle_refresh,
        )

    def _handle_refresh(self, reply: QNetworkReply) -> None:
        payload = self._json(reply)
        if reply.error() != QNetworkReply.NetworkError.NoError or payload.get('error'):
            self._clear_session('Your GitHub session expired. Please sign in again.')
            return
        self._accept_token(payload)

    def _load_user(self) -> None:
        if self._token is None:
            return
        self._set_state('checking_account')
        self._authenticated_get(AUTHENTICATED_USER_URL, self._handle_user)

    def _handle_user(self, reply: QNetworkReply) -> None:
        payload = self._json(reply)
        status_code = int(reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute) or 0)
        if reply.error() != QNetworkReply.NetworkError.NoError or status_code != 200:
            if status_code == 401 and self._token is not None and self._token.can_refresh():
                self._refresh_token()
            else:
                self._clear_session('GitHub could not validate the saved session.')
            return
        self._login = str(payload.get('login', ''))
        self._display_name = str(payload.get('name') or self._login)
        self._avatar_url = str(payload.get('avatar_url', ''))
        if not self._login:
            self._clear_session('GitHub returned an incomplete account profile.')
            return
        self._set_state('signed_in')

    def _clear_session(self, error: str = '') -> None:
        self._poll_timer.stop()
        self._token_store.clear()
        self._token = None
        self._login = ''
        self._display_name = ''
        self._avatar_url = ''
        self._repositories = []
        self._repositories_loading = False
        self._repositories_error = ''
        self._issue_creation_observation_id = 0
        self._issue_creation_error_observation_id = 0
        self._issue_creation_error = ''
        self._issue_queue = []
        self._active_issue_observation_ids = []
        self._issue_batch_total = 0
        self._issue_batch_completed = 0
        self.repositoriesChanged.emit()
        self._device_code = ''
        self._user_code = ''
        self._verification_uri = ''
        self._set_state(
            'error' if error else ('idle' if self._client_id else 'not_configured'), error
        )

    @Slot()
    def openVerificationPage(self) -> None:  # noqa: N802
        """Open GitHub's trusted device-verification page in the default browser."""
        if self._verification_uri:
            from PySide6.QtGui import QDesktopServices

            QDesktopServices.openUrl(QUrl(self._verification_uri))

    @Slot()
    def copyUserCode(self) -> None:  # noqa: N802
        """Copy the device code to the system clipboard."""
        if self._user_code:
            from PySide6.QtGui import QGuiApplication

            QGuiApplication.clipboard().setText(self._user_code)

    @Slot()
    def signOut(self) -> None:  # noqa: N802
        """Forget local GitHub credentials and account state."""
        self._clear_session()
