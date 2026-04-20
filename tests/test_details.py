"""
Tests for the agent's system detail helpers.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetHostname:

    def test_returns_a_string(self):
        from openepm_agent.details import get_hostname
        result = get_hostname()
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetMacAddress:

    @patch("openepm_agent.details._get_wireless_interface", return_value=None)
    @patch("openepm_agent.details._get_any_active_interface")
    def test_falls_back_to_any_interface(self, mock_any, mock_wireless):
        mock_any.return_value = ("eth0", "AA:BB:CC:DD:EE:FF")
        from openepm_agent.details import get_mac_address
        result = get_mac_address()
        assert result == "AA:BB:CC:DD:EE:FF"

    @patch("openepm_agent.details._get_wireless_interface", return_value=None)
    @patch("openepm_agent.details._get_any_active_interface", return_value=(None, None))
    def test_raises_when_no_interface_found(self, mock_any, mock_wireless):
        from openepm_agent.details import get_mac_address
        with pytest.raises(RuntimeError, match="No suitable network interface"):
            get_mac_address()


class TestGetLinuxFamily:

    @patch("distro.id",   return_value="ubuntu")
    @patch("distro.like", return_value="")
    def test_ubuntu_is_debian(self, mock_like, mock_id):
        from openepm_agent.details import get_linux_family
        assert get_linux_family() == "debian"

    @patch("distro.id",   return_value="arch")
    @patch("distro.like", return_value="")
    def test_arch_is_arch(self, mock_like, mock_id):
        from openepm_agent.details import get_linux_family
        assert get_linux_family() == "arch"

    @patch("distro.id",   return_value="fedora")
    @patch("distro.like", return_value="")
    def test_unknown_returns_linux(self, mock_like, mock_id):
        from openepm_agent.details import get_linux_family
        assert get_linux_family() == "linux"
