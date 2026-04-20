export OPENEPM_SERVER_URL="http://192.168.1.243:5000"
export OPENEPM_BOOTSTRAP_SECRET="my-bootstrap-secret"

python -c "from openepm_agent.runner import register; print(register())"
