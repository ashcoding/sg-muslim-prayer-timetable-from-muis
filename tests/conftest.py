"""Fixtures for testing."""
import pytest
import pytest_socket

# Mock pytest_socket to prevent it from blocking/intercepting sockets during tests on Windows
def dummy_no_op(*args, **kwargs):
    pass

pytest_socket.socket_allow_hosts = dummy_no_op
pytest_socket.disable_socket = dummy_no_op
pytest_socket.enable_socket = dummy_no_op

pytest_plugins = ["pytest_homeassistant_custom_component"]

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for testing."""
    yield




