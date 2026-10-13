"""Install manifest-based plugins from local or GitHub-hosted ZIP archives.

Author: Taylor B. | Inspyre-Softworks.
"""

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen
import zipfile


MANIFEST_NAME = 'inspyred-plugin.json'
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
PLUGIN_ID_PATTERN = re.compile(r'^[a-z0-9][a-z0-9._-]{1,63}$')


@dataclass(frozen=True)
class InstalledPluginManifest:
    """Validated metadata for one user-installed plugin."""

    plugin_id: str
    name: str
    version: str
    entry_point: str
    root: Path


class PluginInstallError(RuntimeError):
    """Report an invalid source, archive, or plugin manifest."""


def read_manifest(root: Path) -> InstalledPluginManifest:
    """Read and validate a plugin manifest located at ``root``."""
    manifest_path = root / MANIFEST_NAME
    try:
        payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PluginInstallError(f'Could not read {MANIFEST_NAME}.') from error
    if not isinstance(payload, dict):
        raise PluginInstallError('The plugin manifest must contain a JSON object.')
    plugin_id = str(payload.get('id', '')).strip().casefold()
    name = str(payload.get('name', '')).strip()
    version = str(payload.get('version', '')).strip()
    entry_point = str(payload.get('entry_point', '')).strip()
    if not PLUGIN_ID_PATTERN.fullmatch(plugin_id):
        raise PluginInstallError('The plugin manifest has an invalid ID.')
    if not name or not version:
        raise PluginInstallError('The plugin manifest must include a name and version.')
    module_name, separator, object_name = entry_point.partition(':')
    if not separator or not module_name.isidentifier() or not object_name.isidentifier():
        raise PluginInstallError(
            'entry_point must use a top-level module or package and object, such as plugin:Plugin.'
        )
    module_file = root / f'{module_name}.py'
    package_file = root / module_name / '__init__.py'
    if not module_file.is_file() and not package_file.is_file():
        raise PluginInstallError('The manifest entry-point module is missing from the archive.')
    return InstalledPluginManifest(plugin_id, name, version, entry_point, root)


def github_archive_url(source: str) -> str:
    """Normalize a GitHub repository or archive URL to a downloadable ZIP URL."""
    parsed = urlparse(source.strip())
    if parsed.scheme != 'https' or parsed.hostname not in {'github.com', 'www.github.com'}:
        if parsed.scheme == 'https' and parsed.hostname == 'codeload.github.com':
            return source.strip()
        raise PluginInstallError('Remote plugins must come from an HTTPS GitHub URL.')
    parts = [unquote(part) for part in parsed.path.split('/') if part]
    if len(parts) < 2:
        raise PluginInstallError('Enter a GitHub repository or ZIP URL.')
    owner, repository = parts[:2]
    repository = repository.removesuffix('.git')
    if any(value in {'.', '..'} for value in (owner, repository)):
        raise PluginInstallError('The GitHub repository URL is invalid.')
    if len(parts) == 2:
        return f'https://api.github.com/repos/{quote(owner)}/{quote(repository)}/zipball'
    if len(parts) >= 4 and parts[2] == 'tree':
        reference = '/'.join(parts[3:])
        return (
            f'https://api.github.com/repos/{quote(owner)}/{quote(repository)}/'
            f'zipball/{quote(reference, safe="")}'
        )
    if parsed.path.casefold().endswith('.zip'):
        return source.strip()
    raise PluginInstallError('The GitHub URL must identify a repository, branch, or ZIP archive.')


def _download(source: str, destination: Path) -> None:
    request = Request(github_archive_url(source), headers={'User-Agent': 'Inspyred-Dev'})
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - URL is GitHub-only
            declared_size = int(response.headers.get('Content-Length', 0) or 0)
            if declared_size > MAX_ARCHIVE_BYTES:
                raise PluginInstallError('The plugin archive is larger than 50 MB.')
            total = 0
            with destination.open('wb') as output:
                while chunk := response.read(64 * 1024):
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise PluginInstallError('The plugin archive is larger than 50 MB.')
                    output.write(chunk)
    except PluginInstallError:
        raise
    except OSError as error:
        raise PluginInstallError(f'GitHub download failed: {error}') from error


def _archive_path(source: str, temporary_directory: Path) -> Path:
    parsed = urlparse(source.strip())
    if parsed.scheme in {'https', 'http'}:
        archive = temporary_directory / 'plugin.zip'
        _download(source, archive)
        return archive
    if parsed.scheme == 'file':
        value = unquote(parsed.path)
        if parsed.netloc:
            value = f'//{parsed.netloc}{value}'
        path = Path(value.lstrip('/') if re.match(r'^/[A-Za-z]:/', value) else value)
    else:
        path = Path(source.strip())
    if not path.is_file() or path.suffix.casefold() != '.zip':
        raise PluginInstallError('Choose an existing ZIP file or enter a GitHub URL.')
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise PluginInstallError('The plugin archive is larger than 50 MB.')
    return path


def _safe_extract(archive: Path, destination: Path) -> None:
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.infolist()
            if not members:
                raise PluginInstallError('The plugin ZIP is empty.')
            if (
                len(members) > 5000
                or sum(member.file_size for member in members) > MAX_ARCHIVE_BYTES
            ):
                raise PluginInstallError('The expanded plugin archive is larger than 50 MB.')
            for member in members:
                normalized_name = member.filename.replace('\\', '/')
                path = PurePosixPath(normalized_name)
                if (
                    path.is_absolute()
                    or '..' in path.parts
                    or (path.parts and ':' in path.parts[0])
                ):
                    raise PluginInstallError('The plugin ZIP contains an unsafe path.')
                mode = member.external_attr >> 16
                if mode & 0o170000 == 0o120000:
                    raise PluginInstallError('Symbolic links are not allowed in plugin ZIPs.')
            bundle.extractall(destination)
    except zipfile.BadZipFile as error:
        raise PluginInstallError('The selected file is not a valid ZIP archive.') from error


def install_plugin_archive(
    source: str,
    plugin_directory: Path,
    reserved_ids: set[str] | None = None,
) -> InstalledPluginManifest:
    """Validate and install a plugin archive, replacing the same user plugin if present."""
    plugin_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='inspyred-plugin-') as temporary_name:
        temporary = Path(temporary_name)
        archive = _archive_path(source, temporary)
        extracted = temporary / 'extracted'
        extracted.mkdir()
        _safe_extract(archive, extracted)
        manifests = sorted(extracted.rglob(MANIFEST_NAME), key=lambda path: len(path.parts))
        if len(manifests) != 1:
            raise PluginInstallError(
                f'The plugin ZIP must contain exactly one {MANIFEST_NAME} file.'
            )
        manifest = read_manifest(manifests[0].parent)
        if reserved_ids and manifest.plugin_id in reserved_ids:
            raise PluginInstallError('The plugin ID conflicts with an installed plugin.')
        target = (plugin_directory / manifest.plugin_id).resolve()
        if target.parent != plugin_directory.resolve():
            raise PluginInstallError('The plugin ID resolves outside the plugin directory.')
        if target.exists():
            raise PluginInstallError('This plugin is already installed. Uninstall it first.')
        staged = plugin_directory / f'.{manifest.plugin_id}.installing'
        if staged.exists():
            shutil.rmtree(staged)
        shutil.copytree(manifest.root, staged)
        staged.replace(target)
        return read_manifest(target)
