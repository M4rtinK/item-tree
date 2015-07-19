import urllib2
import tarfile

class ProgressHook(object):
    def __init__(self):
        self._size = 0
        self._done_size = 0.0
        self._progress = 0.0

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size

    @property
    def done_size(self):
        return self._done_size

    @done_size.setter
    def done_size(self, done_size):
        self._done_size = done_size
        self.progress_updated(self.progress)

    @property
    def progress(self):
        try:
            return self.done_size / float(self.size)
        except ZeroDivisionError:
            return 0.0

    def progress_updated(self, progress):
        """Subclass ProgressHook and implement this function to monitor progress."""
        pass

class FileObjectWrapper(object):
    """A file object wrapper used for download progress reporting."""

    def __init__(self, file_object, progress_hook):
        self._file_object = file_object
        self._progress_hook = progress_hook

    def read(self, size=None):
        if size:  # avoid division by zero
            self._progress_hook.done_size += size
            print(self._progress_hook.progress)
            return self._file_object.read(size)
        else:
            return self._file_object.read()

def download_and_unpack(url, path, progress_hook=None):
    if progress_hook is None:
        # use a fake progress hook if none is provided
        progress_hook = ProgressHook()
    print("opening request")
    request = urllib2.urlopen(url)
    print("getting request size")
    request_size = request.headers.get('content-length')
    if request_size:
        progress_hook.size = int(request_size)
    print("wrapping request")
    request_wrapper = FileObjectWrapper(request, progress_hook)
    print("opening tarfile")
    tar_file = tarfile.open(mode="r|gz", fileobj=request_wrapper, bufsize=1024*1024)
    print("extracting tarfile")
    tar_file.extractall(path=path)


def item_tree_from_folder(path, handle_dirs, handle_files):
    pass

def dir_to_item_tree(path, name, parent):
    pass

def file_to_item_tree(path, name, parent):
    pass