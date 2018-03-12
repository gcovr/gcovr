# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
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


def drain(queue):
    """
    Drain a queue of all items
    """
    sentinel_count = 0
    while True:
        try:
            work, args, kwargs = queue.get(False)
            if not work:
                sentinel_count += 1
        except Empty:
            break
    for _ in range(0, 1 + sentinel_count):
        queue.put((None, None, None))


def worker(queue, context, exceptions):
    """
    Run work items from the queue until the sentinal
    None value is hit
    """
    while True:
        work, args, kwargs = queue.get(True)
        if not work:
            queue.put((None, None, None))
            break
        kwargs.update(context)
        try:
            work(*args, **kwargs)
        except:  # noqa: E722
            drain(queue)
            import sys
            exceptions.append(sys.exc_info())
            break


class Workers(object):
    """
    Create a thread-pool which can be given work via an
    add method and will run until work is complete
    """

    def __init__(self, number, context):
        assert(number >= 1)
        self.q = Queue()
        self.exceptions = []
        self.contexts = [context() for _ in range(0, number)]
        self.workers = [Thread(target=worker, args=(self.q, c, self.exceptions)) for c in self.contexts]
        for w in self.workers:
            w.start()

    def add(self, work, *args, **kwargs):
        """
        Add in a method and the arguments to be used
        when running it
        """
        if not work or not self.exceptions:
            self.q.put((work, args, kwargs))

    def size(self):
        """
        Run the size of the thread pool
        """
        return len(self.workers)

    def wait(self):
        """
        Wait until all work is complete
        """
        for w in self.workers:
            self.add(None)
        for w in self.workers:
            while w.is_alive():
                w.join(timeout=0.1)
        for exc_type, exc_obj, exc_trace in self.exceptions:
            import traceback
            traceback.print_exception(exc_type, exc_obj, exc_trace)
        if self.exceptions:
            raise self.exceptions[0][1]
        return self.contexts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            drain(self.q)
        self.wait()
