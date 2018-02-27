# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.


from threading import Thread, Condition
from contextlib import contextmanager

import sys
if sys.version_info[0] >= 3:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty


class LockedDirectories(object):
    """
    Class that keeps a list of locked directories
    """
    def __init__(self):
        self.dirs = set()
        self.cv = Condition()

    def run_in(self, dir_):
        """
        Start running in the directory and lock it
        """
        self.cv.acquire()
        while dir_ in self.dirs:
            self.cv.wait()
        self.dirs.add(dir_)
        self.cv.release()

    def done(self, dir_):
        """
        Finished with the directory, unlock it
        """
        self.cv.acquire()
        self.dirs.remove(dir_)
        self.cv.notify_all()
        self.cv.release()


@contextmanager
def locked_directory(dir_):
    """
    Context for doing something in a locked directory
    """
    locked_directory.global_object.run_in(dir_)
    yield
    locked_directory.global_object.done(dir_)


locked_directory.global_object = LockedDirectories()


class WorkThread(Thread):
    """
    The work thread class continuously gets work and
    completes it
    """
    def __init__(self, pool):
        """
        Initialise with a reference to the pool object
        which houses the queue
        """
        super(WorkThread, self).__init__()
        import tempfile
        self.pool = pool
        self.workdir = tempfile.mkdtemp()

    def run(self):
        """
        Run until the queue is empty
        """
        while True:
            try:
                work, args, kwargs = self.pool.get()
            except Empty:
                break
            kwargs['workdir'] = self.workdir
            work(*args, **kwargs)

    def close(self):
        """
        Empty the working directory
        """
        import shutil

        # On Windows the files may still be in use. This
        # is unlikely, the files are small, and are in a
        # temporary directory so we can skip this.
        shutil.rmtree(self.workdir, ignore_errors=True)


class Workers(object):
    """
    Create a thread-pool which can be given work via an
    add method and will run until work is complete
    """

    def __init__(self, number=0):
        """
        Initialise with a number of workers
        """
        self.q = Queue()
        if number == 0:
            from multiprocessing import cpu_count
            number = cpu_count()
        self.workers = [WorkThread(self) for _ in range(0, number)]

    def add(self, work, *args, **kwargs):
        """
        Add in a method and the arguments to be used
        when running it
        """
        self.q.put((work, args, kwargs))

    def size(self):
        """
        Run the size of the thread pool
        """
        return len(self.workers)

    def get(self):
        """
        Get the next piece of work
        """
        return self.q.get(False, 5)

    def wait(self):
        """
        Wait until all work is complete
        """
        for w in self.workers:
            w.start()
        for w in self.workers:
            w.join()
        for w in self.workers:
            w.close()
