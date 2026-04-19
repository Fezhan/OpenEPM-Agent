#Config imports
python -c "from openepm_agent.config import SERVER_URL, POLL_INTERVAL, BOOTSTRAP_SECRET, CONFIG_FILE; print(SERVER_URL); print(POLL_INTERVAL); print(BOOTSTRAP_SECRET); print(CONFIG_FILE)"

#Environment override
OPENEPM_SERVER_URL=http://192.168.1.50:5000 python -c "from openepm_agent.config import SERVER_URL; print(SERVER_URL)"

#Runner state test
python - <<'PY'
from openepm_agent.runner import save_state, load_state
save_state({"agent_id": 123, "auth_token": "test-token"})
print(load_state())
PY

#mac address
python - <<'PY'
from openepm_agent.details import get_wireless_interface, get_mac_address
print("Wireless interface:", get_wireless_interface())
print("Wireless MAC:", get_mac_address())
PY
