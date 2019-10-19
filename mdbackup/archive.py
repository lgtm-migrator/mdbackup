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

from mdbackup.actions.runner import run_task_actions
from mdbackup.config import CloudConfig


def archive_folder(backup_path: Path, folder: Path, cloud_config: CloudConfig) -> str:
    """
    Given a folder of a backup, archives it into a ``tar`` file and, optionally, compresses the file using different
    strategies. By default, no compression is done.

    A strategy function must be a function that returns a tuple of the command to execute (as pipe) for compress the
    ``tar`` file and the extension to add to the file name. There's some predefined strategies that you can
    use to compress the folder, all available in this package.

    The returned value is the file name for the archived folder.
    """
    logger = logging.getLogger(__name__)
    filename = folder.parts[-1] + '.tar'
    actions = [
        {'from-directory': str(folder)},
        {'tar': None},
    ]

    if cloud_config.compression_strategy is not None:
        actions.append({
            f'compress-{cloud_config.compression_strategy}': {
                'level': cloud_config.compression_level,
            },
        })
        filename += f'.{cloud_config.compression_strategy}'
    if cloud_config.cypher_strategy is not None:
        actions.append({
            f'encrypt-gpg': {
                'passphrase': cloud_config.cypher_params.get('passphrase'),
                'recipients': cloud_config.cypher_params.get('keys', []),
                'algorithm': cloud_config.cypher_params.get('algorithm'),
            },
        })
        filename += '.asc'

    actions.append({'to-file': {'_backup_path': backup_path, 'to': filename}})

    # Do the compression
    logger.info(f'Compressing directory {folder} into {filename}')
    run_task_actions('archive-folder', actions)

    return filename
