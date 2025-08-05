#!/bin/zsh

set -eo pipefail


cd /Users/koen/workspace/toolbox/packages/slack_mcp
ssh nsai-aggregator-gpu "rm -rf /home/azureuser/slack_mcp"
zip -r - .  -x "**.venv/*" -x ".git/*" -x "data/*" | ssh nsai-aggregator-gpu "cat > /home/azureuser/archive.zip && rm -rf /home/azureuser/toolbox && unzip /home/azureuser/archive.zip -d /home/azureuser/slack_mcp"


echo 'installing'
ssh nsai-aggregator-gpu bash -c "
set -eo pipefail
export PATH=/home/azureuser/.local/bin:\$PATH
cd /home/azureuser/slack_mcp
uv venv
source .venv/bin/activate
uv pip install -e . || true
uv pip install --group embeddings || true
"
echo 'killing'

set +e pipefail

ssh nsai-aggregator-gpu <<'EOF'
pkill -f slack_mcp
EOF

set -e pipefail
sleep 3

echo 'starting'
ssh nsai-aggregator-gpu bash -c "
set -eo pipefail
export USE_MOCK_EMBEDDINGS=False
export NOMIC_SECRET_KEY=$NOMIC_SECRET_KEY
export NOMIC_PORT=8020

cd /home/azureuser/slack_mcp
source .venv/bin/activate
nohup python slack_mcp/remote_server/nomic_app.py > output_nomic.log 2>&1 &
"

sleep 1
ssh nsai-aggregator-gpu "
tail -f /home/azureuser/slack_mcp/output_nomic.log
"
