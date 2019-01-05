# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2018  Melchor Alejo Garau Madrigal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
from pathlib import Path
import subprocess
from typing import List, Optional, Callable, Tuple, NewType


StrategyCallable = NewType('StrategyCallable', Callable[[], Tuple[str, str]])


def archive_folder(backup_path: Path, folder: Path, strategies: List[StrategyCallable]=None) -> str:
    """
    Given a folder of a backup, archives it into a ``tar`` file and, optionally, compresses the file using different
    strategies. By default, no compression is done.

    A strategy function must be a function that returns a tuple of the command to execute (as pipe) for compress the
    ``tar`` file and the extension to add to the file name. There's some predefined strategies that you can
    use to compress the folder, all available in this package.

    The returned value is the file name for the archived folder.
    """
    if strategies is None:
        strategies = []
    logger = logging.getLogger(__name__)
    filename = folder.parts[-1] + '.tar'
    directory = folder.relative_to(backup_path)
    logger.info(f'Compressing directory {folder} into {filename}')

    if len(strategies) == 0:
        end_cmd = f' > "{filename}"'
    else:
        for strategy in strategies:
            cmd, ext = strategy()
            filename += ext
            end_cmd = f'| {cmd}'

    # Do the compression
    logger.debug(f'Executing command ["bash", "-c", \'tar -c "{str(directory)}" {end_cmd} > "{filename}"\']')
    _exec = subprocess.run(['bash', '-c', f'tar -c "{str(directory)}" {end_cmd} > "{filename}"'],
                           cwd=str(backup_path), check=True)

    return filename


def gzip_strategy(level: int = 5) -> StrategyCallable:
    """
    Compression strategy that uses ``gzip`` to compress the ``tar`` file.
    """
    def gzip():
        return f'gzip -{level}', '.gz'

    return gzip


def xz_strategy(level: int = 5) -> StrategyCallable:
    """
    Compression strategy that uses ``xz`` to compress the ``tar`` file.
    """
    def xz():
        return f'xz -z -T 0 -{level} -c -', '.xz'

    return xz


COMPRESSION_STRATEGIES = {
    'gzip': gzip_strategy,
    'xz': xz_strategy,
}


def get_compression_strategy(strategy_name: str, level: Optional[int]) -> Callable:
    func = COMPRESSION_STRATEGIES.get(strategy_name.lower())
    if func is not None:
        return func(level)
    else:
        raise KeyError(f'Unknown compression strategy "{strategy_name}"')


def gpg_passphrase_strategy(passphrase: str) -> StrategyCallable:
    """
    Compression and encryption strategy that uses ``gpg`` (using passphrase) to compress and encrypt the ``tar`` file.
    """
    def gpg():
        return f'gpg --compress-algo 0 --output - --batch --passphrase "{passphrase}" --symmetric -', '.asc'

    return gpg


def gpg_key_strategy(keys: List[str]) -> StrategyCallable:
    """
    Compression and encryption strategy that uses ``gpg`` (using a key) to compress and encrypt the ``tar`` file.
    """
    def gpg():
        recv = ' '.join([f'-r {email}' for email in keys])
        return f'gpg --compress-algo 0 --output - --encrypt {recv} -', '.asc'

    return gpg


CYPHER_STRATEGIES = {
    'gpg-passphrase': gpg_passphrase_strategy,
    'gpg-keys': gpg_key_strategy,
}


def get_cypher_strategy(strategy_name: str, **kwargs) -> StrategyCallable:
    func = CYPHER_STRATEGIES.get(strategy_name.lower())
    if func is not None:
        return func(**kwargs)
    else:
        raise KeyError(f'Unknown cypher strategy "{strategy_name}"')