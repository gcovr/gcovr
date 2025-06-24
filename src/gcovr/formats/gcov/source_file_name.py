import logging
import os
from typing import Optional
from ...utils import (
    commonpath,
    fix_case_of_path,
    is_fs_case_insensitive,
)

LOGGER = logging.getLogger("gcovr")


def guess_source_file_name(
    source_from_gcov: str,
    data_fname: str,
    gcda_fname: Optional[str],
    root_dir: str,
    starting_dir: str,
    obj_dir: Optional[str],
    current_dir: Optional[str] = None,
) -> str:
    """Guess the full source filename."""
    if current_dir is None:
        current_dir = os.getcwd()
    if os.path.isabs(source_from_gcov):
        fname = source_from_gcov
    elif gcda_fname is None:
        fname = guess_source_file_name_via_aliases(
            source_from_gcov, data_fname, current_dir
        )
    else:
        fname = guess_source_file_name_heuristics(
            source_from_gcov,
            data_fname,
            gcda_fname,
            current_dir,
            root_dir,
            starting_dir,
            obj_dir,
        )

    if is_fs_case_insensitive():
        fname = fix_case_of_path(fname)

    LOGGER.debug(
        f"Finding source file corresponding to a gcov data file\n"
        f"  gcov_fname   {data_fname}\n"
        f"  current_dir  {current_dir}\n"
        f"  root         {root_dir}\n"
        f"  starting_dir {starting_dir}\n"
        f"  obj_dir      {obj_dir}\n"
        f"  gcda_fname   {gcda_fname}\n"
        f"  --> fname    {fname}"
    )

    return fname


def guess_source_file_name_via_aliases(
    source_from_gcov: str,
    data_fname: str,
    current_dir: str,
) -> str:
    """Guess the full source filename with path by an alias."""
    common_dir = commonpath([data_fname, current_dir])
    fname = os.path.abspath(os.path.join(common_dir, source_from_gcov))
    if os.path.exists(fname):
        return fname

    initial_fname = fname

    data_fname_dir = os.path.dirname(data_fname)
    fname = os.path.abspath(os.path.join(data_fname_dir, source_from_gcov))
    if os.path.exists(fname):
        return fname

    # @latk-2018: The original code is *very* insistent
    # on returning the initial guess. Why?
    return initial_fname


def guess_source_file_name_heuristics(  # pylint: disable=too-many-return-statements
    source_from_gcov: str,
    data_fname: str,
    gcda_fname: str,
    current_dir: str,
    root_dir: str,
    starting_dir: str,
    obj_dir: Optional[str],
) -> str:
    """Guess the full source filename with path by a heuristic."""
    # 0. Try using the path to the gcov file
    fname = os.path.join(os.path.dirname(data_fname), source_from_gcov)
    if os.path.exists(fname):
        return fname

    LOGGER.debug("Fallback to heuristic of gcovr 5.1")

    # 1. Try using the current working directory as the source directory
    fname = os.path.join(current_dir, source_from_gcov)
    if os.path.exists(fname):
        return fname

    # 2. Try using the path to common prefix with the root_dir as the source directory
    fname = os.path.join(root_dir, source_from_gcov)
    if os.path.exists(fname):
        return fname

    # 3. Try using the starting directory as the source directory
    fname = os.path.join(starting_dir, source_from_gcov)
    if os.path.exists(fname):
        return fname

    # 4. Try using relative path from object dir
    if obj_dir is not None:
        fname = os.path.normpath(os.path.join(obj_dir, source_from_gcov))
        if os.path.exists(fname):
            return fname

    # Get path of gcda file
    gcda_fname_dir = os.path.dirname(gcda_fname)

    # 5. Try using the path to the gcda as the source directory
    fname = os.path.join(gcda_fname_dir, source_from_gcov)
    if os.path.exists(fname):
        return os.path.normpath(fname)

    # 6. Try using the path to the gcda file as the source directory, removing the path part from the gcov file
    fname = os.path.join(gcda_fname_dir, os.path.basename(source_from_gcov))
    return fname
