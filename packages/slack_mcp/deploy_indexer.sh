#!/bin/zsh

set -eo pipefail


cd /Users/koen/workspace/toolbox/packages/slack_mcp
ssh toolbox-prod "rm -rf /home/azureuser/slack_mcp"
zip -r - .  -x "**.venv/*" -x ".git/*" -x "data/*" | ssh toolbox-prod "cat > /home/azureuser/archive.zip && rm -rf /home/azureuser/toolbox && unzip /home/azureuser/archive.zip -d /home/azureuser/slack_mcp"


echo 'installing'
ssh toolbox-prod bash -c "
set -eo pipefail
export PATH=/home/azureuser/.local/bin:\$PATH
cd /home/azureuser/slack_mcp
uv venv
source .venv/bin/activate
uv pip install -e . || true
"

echo 'killing'

set +e pipefail

ssh toolbox-prod <<'EOF'
pkill -f slack_mcp
EOF

set -e pipefail
sleep 3

echo 'starting'
ssh toolbox-prod bash -c "
set -eo pipefail
export NOMIC_URL=http://4.151.234.109
export NOMIC_PORT=8020
export NOMIC_SECRET_KEY=$NOMIC_SECRET_KEY
export USE_MOCK_EMBEDDINGS=False
export SERVER_PORT=8005

cd /home/azureuser/slack_mcp
source .venv/bin/activate
nohup python slack_mcp/remote_server/remote_app.py > output_slack_server.log 2>&1 &
"

sleep 1
ssh toolbox-prod "
tail -f /home/azureuser/slack_mcp/output_slack_server.log
"
