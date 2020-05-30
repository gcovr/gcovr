
def pytest_addoption(parser):  # pragma: no cover
    parser.addoption("--generate_reference", action="store_true", help="Generate the reference")
    parser.addoption("--update_reference", action="store_true", help="Update the reference")
    parser.addoption("--skip_clean", action="store_true", help="Skip the clean after the test")
