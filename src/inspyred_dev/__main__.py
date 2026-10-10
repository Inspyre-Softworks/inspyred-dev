"""Application entry point.

Author: Taylor B. | Inspyre-Softworks.
"""

import argparse
from collections.abc import Sequence

from inspyred_dev import __version__


def _build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog='inspyred-dev',
        description='Capture developer observations and turn them into actionable work.',
    )
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line options and start Inspyred Dev.

    Parameters
    ----------
    argv : Sequence[str] | None
        Arguments to parse without the executable name. When omitted, arguments
        are read from :data:`sys.argv`.

    Returns
    -------
    int
        The desktop application's process exit code. Help and version requests
        terminate through :class:`SystemExit`, as defined by :mod:`argparse`.
    """
    _build_parser().parse_args(argv)

    # Import Qt only when launching the GUI so --help and --version stay fast
    # and remain available in minimal packaging environments.
    from inspyred_dev.gui.app import run

    return run()


if __name__ == '__main__':
    raise SystemExit(main())
