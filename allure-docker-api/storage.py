from abc import ABC, abstractmethod
import s3fs
import os
import shutil
import glob

class StorageInterface(ABC):
    @abstractmethod
    def isdir(self, path):
        pass

    @abstractmethod
    def isfile(self, path):
        pass

    @abstractmethod
    def getmtime(self, path):
        pass

    @abstractmethod
    def listdir(self, path):
        pass

    @abstractmethod
    def mkdir(self, path):
        pass

    @abstractmethod
    def remove(self, path):
        pass

    @abstractmethod
    def rmdir(self, path):
        pass

    @abstractmethod
    def exists(self, path):
        pass

    @abstractmethod
    def save_file(self, file, path):
        pass

    @abstractmethod
    def save_json(self, content, path):
        pass

    @abstractmethod
    def read_file(self, path):
        pass

    @abstractmethod
    def copy_dir(self, source_path, dest_path):
        pass

class LocalStorage(StorageInterface):
    def __init__(self):
        self.type = 'local'

    def isdir(self, path):
        return os.path.isdir(path)

    def isfile(self, path):
        return os.path.isfile(path)

    def getmtime(self, path):
        return os.path.getmtime(path)

    def listdir(self, path):
        return os.listdir(path)
    
    def glob(self, pathname):
        return glob.glob(pathname)

    def mkdir(self, path):
        return os.makedirs(path, exist_ok=True)

    def rmdir(self, path):
        shutil.rmtree(path)

    def remove(self, path):
        os.remove(path)

    def exists(self, path):
        return os.path.exists(path)

    def save_file(self, file, path, method):
        file.save(path)

    def write_file(self, file, path, method):
        with open(path, method) as f:
            if hasattr(file, 'read'):
                f.write(file.read())
            else:
                f.write(file)

    def save_json(self, content, path):
        file = open(path, "wb")
        file.write(content)

    def read_file(self, path):
        with open(path, 'rb') as f:
            content = f.read()
            return content

    def copy_dir(self, source_path, dest_path):
        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)


class S3Storage(StorageInterface):
    def __init__(self, bucket_name):
        self.fs = s3fs.S3FileSystem()
        self.bucket_name = bucket_name
        self.type = 's3'
        self.init_root_folder()
        self.write_file = self.save_file

    def isdir(self, path):
        return self.fs.isdir(f"{self.bucket_name}{path}")

    def isfile(self, path):
        return self.fs.isfile(f"{self.bucket_name}{path}")

    def getmtime(self, path):
        if path.startswith(self.bucket_name):
            path = path[len(self.bucket_name):]
        info = self.fs.info(f"{self.bucket_name}{path}")
        return info['LastModified'].timestamp()

    def listdir(self, path):
        return [item.split('/')[-1] for item in self.fs.ls(f"{self.bucket_name}{path}") if not item.endswith('/')]

    def glob(self, pathname):
        return self.fs.glob(pathname)

    def mkdir(self, path):
        self.fs.touch(f"{self.bucket_name}{path}/dummyfile")

    def rmdir(self, path):
        self.fs.rm(f"{self.bucket_name}{path}", recursive=True)

    def remove(self, path):
        return self.fs.rm(f"{self.bucket_name}{path}")

    def exists(self, path):
        return self.fs.exists(f"{self.bucket_name}{path}")
    
    def save_file(self, file, path, method):
        try:
            with self.fs.open(f"{self.bucket_name}{path}", method) as f:
                if hasattr(file, 'read'):
                    f.write(file.read())
                else:
                    f.write(file)
        except Exception as e:
            return e

    def save_json(self, content, path):
        try:
            with self.fs.open(f"{self.bucket_name}{path}", "wb") as f:
                f.write(content)
        except Exception as e:
            return e

    def read_file(self, path):
        if path.startswith(self.bucket_name):
            path = path[len(self.bucket_name):]
        with self.fs.open(f"{self.bucket_name}{path}", 'rb') as f:
            content = f.read()
            return content

    def copy_dir(self, source_path, dest_path):
        self.fs.copy(f"{self.bucket_name}{source_path}/", f"{self.bucket_name}{dest_path}/", recursive=True)
    
    # s3 specific methods

    def get_files(self, source_path, dest_path):
        self.fs.get(f"{self.bucket_name}{source_path}", f"{dest_path}/", recursive=True)
    
    def put_files(self, source_path, dest_path):
        self.fs.put(f"{source_path}/", f"{self.bucket_name}{dest_path}", recursive=True)

    def init_root_folder(self):
        base_dir = os.environ['STATIC_CONTENT_PROJECTS']
        if not self.exists(base_dir):
            self.mkdir(base_dir)
    

def get_storage(storage_type, bucket_name=None):
    if storage_type == 'local':
        return LocalStorage()
    elif storage_type == 's3':
        return S3Storage(bucket_name=bucket_name)
    else:
        raise ValueError("Unsupported storage type")
