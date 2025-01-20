# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import logging
from sys import exc_info
from threading import Thread, Condition, RLock
from traceback import format_exception
from contextlib import contextmanager
from queue import Queue, Empty
from typing import Any, Callable, Iterator, Optional

LOGGER = logging.getLogger("gcovr")


class LockedDirectories:
    """
    Class that keeps a list of locked directories
    """

    def __init__(self) -> None:
        self.dirs = set[str]()
        self.cv = Condition()

    def run_in(self, directory: str) -> None:
        """
        Start running in the directory and lock it
        """
        self.cv.acquire()
        while directory in self.dirs:
            self.cv.wait()
        self.dirs.add(directory)
        self.cv.release()

    def done(self, directory: str) -> None:
        """
        Finished with the directory, unlock it
        """
        self.cv.acquire()
        self.dirs.remove(directory)
        self.cv.notify_all()
        self.cv.release()


locked_directory_global_object = LockedDirectories()


@contextmanager
def locked_directory(directory: str) -> Iterator[None]:
    """
    Context for doing something in a locked directory
    """
    locked_directory_global_object.run_in(directory)
    try:
        yield
    finally:
        locked_directory_global_object.done(directory)


QueueContent = Optional[tuple[Callable[[str], None], tuple[Any], dict[str, Any]]]


def worker(
    queue: "Queue[QueueContent]", context: dict[str, Any], pool: "Workers"
) -> None:
    """
    Run work items from the queue until the sentinel
    None value is hit
    """
    while True:
        entry: QueueContent = queue.get(True)
        if entry is None:
            break
        work: Callable[[str], None]
        args: tuple[str]
        kwargs: dict[str, Any]
        work, args, kwargs = entry
        kwargs.update(context)
        try:
            work(*args, **kwargs)
        except:  # noqa: E722 # pylint: disable=bare-except
            pool.stop_with_exception()
            break


class Workers:
    """
    Create a thread-pool which can be given work via an
    add method and will run until work is complete
    """

    def __init__(self, number: int, context: Callable[[], dict[str, Any]]) -> None:
        if number < 1:
            raise AssertionError("At least one executer is needed.")
        self.q: "Queue[QueueContent]" = Queue()
        self.lock = RLock()
        self.exceptions = list[str]()
        self.contexts = [context() for _ in range(0, number)]
        self.workers = list[Thread](
            [Thread(target=worker, args=(self.q, c, self)) for c in self.contexts]
        )
        for w in self.workers:
            w.start()

    def add(self, work: Any, *args: Any, **kwargs: Any) -> None:
        """
        Add in a method and the arguments to be used
        when running it
        """
        with self.lock:
            # Do not push additional items if there is already an exception
            if self.exceptions:  # pragma: no cover
                return
            self.q.put((work, args, kwargs))

    def add_sentinels(self) -> None:
        """
        Add the sentinels to the end of the queue so
        the threads know to stop
        """
        with self.lock:
            for _ in self.workers:
                self.q.put(None)

    def drain(self) -> None:
        """
        Drain the queue
        """
        with self.lock:
            while True:
                try:
                    self.q.get(False)
                except Empty:
                    break
            self.add_sentinels()

    def stop_with_exception(self) -> None:
        """
        A thread has failed and needs to raise an exception.
        """
        with self.lock:
            self.drain()
            self.exceptions.append("".join(format_exception(*exc_info())))

    def size(self) -> int:
        """
        Run the size of the thread pool
        """
        return len(self.workers)

    def wait(self) -> list[dict[str, Any]]:
        """
        Wait until all work is complete
        """
        self.add_sentinels()
        for w in self.workers:
            # Allow interrupts in Thread.join
            while w.is_alive():
                w.join(timeout=1)
        self.workers = []

        for traceback in self.exceptions:
            LOGGER.error(traceback)

        if self.exceptions:
            raise RuntimeError(
                "Worker thread raised exception, workers canceled."
            ) from None
        return self.contexts

    def __enter__(self) -> "Workers":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.size() != 0:
            raise AssertionError(
                "Sanity check, you must call wait on the contextmanager to get the context of the workers."
            )
