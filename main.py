#!/usr/bin/env python

from __future__ import with_statement

import os
from errno import ENOENT, ENODATA, ENONET
from functools import lru_cache
from stat import S_IFDIR, S_IFLNK, S_IFREG
from time import time
from typing import List

import canvasapi.exceptions
import canvasapi.file
import canvasapi.folder
from canvasapi import Canvas
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

API_URL = 'https://hvl.instructure.com'


class Passthrough(LoggingMixIn, Operations):

    fd = 0

    def __init__(self,  access_token):
        print(f'__init__(self,  "{access_token}")')
        self.now = time()
        self.canvas = Canvas(API_URL, access_token)
        self.user = self.canvas.get_user('self')
        self.open_files = dict()

    @lru_cache
    def _resolve_path(self, path) -> List[canvasapi.folder.Folder]:
        return [*self.user.resolve_path(path)]

    @lru_cache
    def _get_file(self, path) -> canvasapi.file.File:
        try:
            file_path = os.path.join(*os.path.split(path)[:-1])
            file_name = os.path.split(path)[-1]

            folder = self._resolve_path(file_path)[-1]
            fc = [*filter(lambda f: f.display_name == file_name, folder.get_files())]
            return fc[0]
        except IndexError:
            raise FuseOSError(ENOENT)

    @lru_cache
    def getattr(self, path, fh=None):
        print(f'getattr(self, "{path}", {fh})')

        try:
            folders = self._resolve_path(path)
            folder: canvasapi.folder.Folder
            folder = folders[-1]

            return dict(
                st_mode=(S_IFDIR | 0o755),
                st_ino=folder.id,
                st_ctime=folder.created_at_date.toordinal(),
                st_mtime=folder.updated_at_date.toordinal(),
                st_atime=folder.updated_at_date.toordinal(),
                st_nlink=2,
                st_uid=os.getuid(),
                st_gid=os.getgid(),
                st_size=folder.files_count + folder.folders_count
            )

        except canvasapi.exceptions.ResourceDoesNotExist:
            file = self._get_file(path)
            return dict(
                st_mode=(S_IFREG | 0o444),
                st_ino=file.id,
                st_ctime=file.created_at_date.toordinal(),
                st_mtime=file.modified_at_date.toordinal(),
                st_atime=file.updated_at_date.toordinal(),
                st_nlink=2,
                st_uid=os.getuid(),
                st_gid=os.getgid(),
                st_size=file.size
            )

    def getxattr(self, path, name, position=0):
        print(f'getxattr(self, {path}, "{name}", {position})')
        raise FuseOSError(ENODATA)

    @lru_cache
    def readdir(self, path, fh):
        print(f'readdir(self, {path}, {fh})')

        rp = self._resolve_path(path)
        if not rp:
            return FuseOSError(ENONET)  # No such file or directory

        rp0: canvasapi.folder.Folder
        rp0 = rp[-1]

        return ['.', '..'] + [x.name for x in rp0.get_folders()] + [x.display_name for x in rp0.get_files()]

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def mkdir(self, path, mode):
        print(f'mkdir(self, {path}, {mode})')
        try:
            parent_folder = os.path.join(*os.path.split(path)[:-1])
            folder_name = os.path.split(path)[-1]

            folder = self._resolve_path(parent_folder)[-1]
            folder.create_folder(folder_name)

            # TODO custom push entry or at least refetch in other thread
            self._resolve_path.cache_clear()
        except IndexError:
            raise FuseOSError(ENOENT)

    def rmdir(self, path):
        print(f'rmdir(self, {path})')
        try:
            folder = self._resolve_path(path)[-1]
            print('folder = ', folder)
            folder.delete()

            # TODO invalidate only single entry
            self._resolve_path.cache_clear()
        except IndexError:
            raise FuseOSError(ENOENT)

    def open(self, path, flags):
        # TODO dont save large files into RAM
        print(f'open(self, {path}, {flags})')
        file: canvasapi.file.File
        file = self._get_file(path)

        # TODO proper error handling
        assert path not in self.open_files

        self.open_files[path] = file.get_contents(binary=True)
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        print(f'read(self, {path}, {size}, {offset}, {fh})')
        return self.open_files[path][offset:offset + size]

    def release(self, path, fh):
        print(f'release(self, {path}, {fh})')
        del self.open_files[path]


def main(mountpoint, access_token):
    print(f'mounting into "{mountpoint}"')
    print(f'll "{mountpoint}/profile pictures/profile.jpg"')
    print(f'tree "{mountpoint}"')
    print(f'mkdir "{mountpoint}/test_folder"')
    print(f'file "{mountpoint}/profile pictures/profile.jpg"')
    FUSE(Passthrough(access_token), mountpoint, nothreads=True, foreground=True, allow_other=True)


if __name__ == '__main__':
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        token = open('token.txt').read().strip()
        main(td, token)
