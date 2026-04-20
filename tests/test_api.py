"""
Tests for the agent HTTP client (api.py).
Uses unittest.mock to avoid a real server.
"""
import pytest
from unittest.mock import patch, MagicMock


def make_response(status_code, json_data):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


class TestRegisterAgent:

    @patch("openepm_agent.api.requests.post")
    def test_register_success(self, mock_post):
        mock_post.return_value = make_response(201, {
            "agent_id": 1,
            "auth_token": "abc123",
            "agent": {},
        })
        from openepm_agent.api import register_agent
        result = register_agent("host", "AA:BB:CC:DD:EE:FF", "debian", "")
        assert result["agent_id"] == 1
        assert result["auth_token"] == "abc123"

    @patch("openepm_agent.api.requests.post")
    def test_register_raises_on_http_error(self, mock_post):
        import requests
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError(response=mock_resp)
        mock_resp.status_code = 403
        mock_post.return_value = mock_resp
        from openepm_agent.api import register_agent
        with pytest.raises(requests.HTTPError):
            register_agent("host", "FF:FF:FF:FF:FF:FF", "debian", "")


class TestHeartbeat:

    @patch("openepm_agent.api.requests.post")
    def test_heartbeat_success(self, mock_post):
        mock_post.return_value = make_response(200, {"status": "ok"})
        from openepm_agent.api import heartbeat
        result = heartbeat(1, "abc123")
        assert result["status"] == "ok"

    @patch("openepm_agent.api.requests.post")
    def test_heartbeat_passes_bearer_token(self, mock_post):
        mock_post.return_value = make_response(200, {"status": "ok"})
        from openepm_agent.api import heartbeat
        heartbeat(1, "mytoken")
        call_kwargs = mock_post.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers", {})
        assert headers.get("Authorization") == "Bearer mytoken"


class TestPollCommand:

    @patch("openepm_agent.api.requests.get")
    def test_poll_returns_none_when_no_command(self, mock_get):
        mock_get.return_value = make_response(200, {"command": None})
        from openepm_agent.api import poll_command
        assert poll_command(1, "token") is None

    @patch("openepm_agent.api.requests.get")
    def test_poll_returns_command(self, mock_get):
        cmd = {"execution_id": 5, "definition": {"name": "ping"}, "parameters": {}}
        mock_get.return_value = make_response(200, {"command": cmd})
        from openepm_agent.api import poll_command
        result = poll_command(1, "token")
        assert result["execution_id"] == 5


class TestSubmitResult:

    @patch("openepm_agent.api.requests.post")
    def test_submit_result_sends_correct_fields(self, mock_post):
        mock_post.return_value = make_response(200, {"message": "ok"})
        from openepm_agent.api import submit_result
        submit_result(
            execution_id=5,
            auth_token="token",
            output="pong",
            error="",
            status="completed",
            exit_code=0,
        )
        call_kwargs = mock_post.call_args
        body = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json", {})
        assert body["output"] == "pong"
        assert body["error"] == ""
        assert body["status"] == "completed"
        assert body["exit_code"] == 0
