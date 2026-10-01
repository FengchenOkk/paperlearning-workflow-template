"""单文件原子写入；同目录暂存，失败保留原件，不留下半截内容。"""
import os
from pathlib import Path
import shutil
import tempfile


def write_bytes(path, content):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('拒绝覆盖符号链接')
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            shutil.copymode(path, temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_text(path, content):
    write_bytes(path, content.encode('utf-8'))


def copy_file(source, target):
    write_bytes(target, Path(source).read_bytes())
    return str(target)


def copy_tree(source, target):
    return shutil.copytree(source, target, copy_function=copy_file)
