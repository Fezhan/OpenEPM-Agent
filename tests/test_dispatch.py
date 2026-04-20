"""
Tests for agent dispatch and built-in command handlers.
No server connection required — all handlers run locally.
"""
import pytest
import json
from unittest.mock import patch, MagicMock


def make_execution(name, command_type="internal", template="", parameters=None, timeout=30):
    return {
        "execution_id": 1,
        "definition": {
            "name": name,
            "command_type": command_type,
            "command_template": template,
            "timeout_seconds": timeout,
        },
        "parameters": parameters or {},
    }


class TestPing:

    def test_ping_returns_pong(self):
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution("ping"))
        assert result["status"] == "completed"
        assert result["stdout"] == "pong"
        assert result["exit_code"] == 0


class TestGetSystemInfo:

    def test_system_info_returns_json(self):
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution("get_system_info"))
        assert result["status"] == "completed"
        data = json.loads(result["stdout"])
        assert "hostname" in data
        assert "cpu_count" in data
        assert "ram_total_gb" in data

    def test_system_info_has_disk_info(self):
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution("get_system_info"))
        data = json.loads(result["stdout"])
        assert "disk_total_gb" in data
        assert "disk_used_pct" in data


class TestGetProcessList:

    def test_process_list_returns_list(self):
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution("get_process_list"))
        assert result["status"] == "completed"
        procs = json.loads(result["stdout"])
        assert isinstance(procs, list)
        assert len(procs) > 0

    def test_process_list_has_expected_fields(self):
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution("get_process_list"))
        procs = json.loads(result["stdout"])
        first = procs[0]
        assert "pid" in first
        assert "name" in first
        assert "status" in first


class TestRestartAgent:

    def test_restart_agent_returns_post_action(self):
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution("restart_agent"))
        assert result["status"] == "completed"
        assert result["_post_action"] == "restart"


class TestUnknownCommand:

    def test_unknown_internal_command_fails(self):
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution("non_existent_command"))
        assert result["status"] == "failed"
        assert "Unknown internal command" in result["stderr"]

    def test_unsupported_command_type_fails(self):
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution("something", command_type="grpc"))
        assert result["status"] == "failed"
        assert "Unsupported command type" in result["stderr"]


class TestShellExecutor:

    def test_shell_template_substitution(self):
        from openepm_agent.dispatch import _render_template
        result = _render_template("df -h {{path}}", {"path": "/home"})
        assert result == "df -h /home"

    def test_shell_template_multiple_params(self):
        from openepm_agent.dispatch import _render_template
        result = _render_template("tail -n {{lines}} {{path}}", {"lines": "50", "path": "/var/log/syslog"})
        assert result == "tail -n 50 /var/log/syslog"

    @patch("subprocess.run")
    def test_shell_command_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution(
            "custom", command_type="shell", template="echo hello"
        ))
        assert result["status"] == "completed"
        assert result["stdout"] == "output"

    @patch("subprocess.run")
    def test_shell_command_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error msg")
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution(
            "custom", command_type="shell", template="false"
        ))
        assert result["status"] == "failed"

    @patch("subprocess.run")
    def test_shell_command_timeout(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)
        from openepm_agent.dispatch import dispatch_command
        result = dispatch_command(make_execution(
            "custom", command_type="shell", template="sleep 999", timeout=1
        ))
        assert result["status"] == "timeout"
