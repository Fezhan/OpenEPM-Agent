"""
Tests for the agent runner (enrollment, state, main loop logic).
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def tmp_state(tmp_path, monkeypatch):
    """Redirect state file to a temp directory for every test."""
    import openepm_agent.runner as runner_module
    import openepm_agent.config as config_module

    config_module.CONFIG_DIR  = tmp_path
    config_module.CONFIG_FILE = tmp_path / "agent.conf"
    runner_module.CONFIG_DIR  = tmp_path
    runner_module.CONFIG_FILE = tmp_path / "agent.conf"
    yield tmp_path


class TestLoadState:

    def test_returns_empty_dict_when_no_file(self, tmp_state):
        from openepm_agent.runner import load_state
        assert load_state() == {}

    def test_returns_empty_dict_on_empty_file(self, tmp_state):
        (tmp_state / "agent.conf").write_text("")
        from openepm_agent.runner import load_state
        assert load_state() == {}

    def test_returns_empty_dict_on_corrupt_json(self, tmp_state):
        (tmp_state / "agent.conf").write_text("{broken json")
        from openepm_agent.runner import load_state
        assert load_state() == {}

    def test_returns_state_when_valid(self, tmp_state):
        (tmp_state / "agent.conf").write_text(
            json.dumps({"agent_id": 1, "auth_token": "abc"})
        )
        from openepm_agent.runner import load_state
        state = load_state()
        assert state["agent_id"] == 1
        assert state["auth_token"] == "abc"


class TestSaveState:

    def test_saves_and_loads_state(self, tmp_state):
        from openepm_agent.runner import save_state, load_state
        save_state({"agent_id": 42, "auth_token": "xyz"})
        state = load_state()
        assert state["agent_id"] == 42

    def test_creates_directory_if_missing(self, tmp_state):
        nested = tmp_state / "nested" / "deep"
        import openepm_agent.runner as r
        r.CONFIG_DIR  = nested
        r.CONFIG_FILE = nested / "agent.conf"
        from openepm_agent.runner import save_state
        save_state({"agent_id": 1, "auth_token": "t"})
        assert (nested / "agent.conf").exists()


class TestEnsureRegistered:

    def test_returns_existing_state_without_calling_server(self, tmp_state):
        (tmp_state / "agent.conf").write_text(
            json.dumps({"agent_id": 5, "auth_token": "existing-token"})
        )
        with patch("openepm_agent.runner.register_agent") as mock_reg:
            from openepm_agent.runner import ensure_registered
            state = ensure_registered()
            assert state["agent_id"] == 5
            mock_reg.assert_not_called()

    def test_registers_when_no_state(self, tmp_state):
        with patch("openepm_agent.runner.register_agent") as mock_reg, \
             patch("openepm_agent.runner.get_hostname", return_value="host"), \
             patch("openepm_agent.runner.get_mac_address", return_value="AA:BB:CC:DD:EE:FF"), \
             patch("openepm_agent.runner.get_linux_family", return_value="debian"):
            mock_reg.return_value = {"agent_id": 10, "auth_token": "new-token"}
            from openepm_agent.runner import ensure_registered
            state = ensure_registered()
            assert state["agent_id"] == 10
            assert state["auth_token"] == "new-token"

    def test_returns_none_on_enrollment_failure(self, tmp_state):
        import requests
        with patch("openepm_agent.runner.register_agent") as mock_reg, \
             patch("openepm_agent.runner.get_hostname", return_value="host"), \
             patch("openepm_agent.runner.get_mac_address", return_value="AA:BB:CC:DD:EE:FF"), \
             patch("openepm_agent.runner.get_linux_family", return_value="debian"):
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            mock_resp.text = "Forbidden"
            mock_reg.side_effect = requests.HTTPError(response=mock_resp)
            from openepm_agent.runner import ensure_registered
            assert ensure_registered() is None
