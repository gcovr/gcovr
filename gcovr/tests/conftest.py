
def pytest_addoption(parser):  # pragma: no cover
    parser.addoption("--generate_reference", action="store_true", help="Generate the reference")
    parser.addoption("--update_reference", action="store_true", help="Update the reference")
    parser.addoption("--archive_differences", action="store_true", help="Archive the different files")
    parser.addoption("--skip_clean", action="store_true", help="Skip the clean after the test")
