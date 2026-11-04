def pytest_configure(config):
    config.addinivalue_line("markers", "browser: tests that launch a real browser")
