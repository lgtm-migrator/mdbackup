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
from typing import Union, List

from b2blaze import B2
from b2blaze.models.bucket import B2Bucket

from mdbackup.storage.storage import AbstractStorage


class B2Storage(AbstractStorage[str]):

    def __init__(self, config):
        self.__log = logging.getLogger(__name__)
        self.__b2 = B2(key_id=config['keyId'], application_key=config['appKey'])
        self.__bucket: B2Bucket = self.__b2.buckets.get(config['bucket'])
        self.__password: str = config.get('password')
        self.__pre = config['backupsPath']

    def list_directory(self, path: Union[str, Path, str]) -> List[str]:
        path = path if isinstance(path, str) else str(path.absolute())
        return [item.file_name for item in self.__bucket.files.all(include_hidden=True)
                if item.file_name.startswith(self.__pre + path)]

    def create_folder(self, name: str, parent: Union[Path, str, str]=None) -> str:
        key = self.__pre + f'{parent.absolute()}/{name}/'
        return key

    def upload(self, path: Path, parent: Union[Path, str, str]=None):
        if isinstance(parent, Path):
            key = f'{parent.absolute()}/{path.name}'
        elif isinstance(parent, str):
            key = f'{parent}/{path.name}'
        else:
            key = path.name
        key = self.__pre + key
        self.__log.info(f'Uploading file {key} (from {path})')
        with open(str(path.absolute()), 'rb') as file_to_upload:
            ret = self.__bucket.files.upload(contents=file_to_upload,
                                             file_name=key,
                                             bucket_name=self.__bucket,
                                             password=self.__password)
        self.__log.debug(ret)
