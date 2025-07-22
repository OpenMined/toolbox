#!/bin/zsh
set -eo pipefail


cd /Users/koen/workspace/toolbox/packages/notes_mcp
zip -r - .  -x "**.venv/*" -x ".git/*" -x "data/*" | ssh toolbox-prod "cat > /home/azureuser/archive.zip && rm -rf /home/azureuser/toolbox && unzip /home/azureuser/archive.zip -d /home/azureuser/toolbox"


echo 'installing'
ssh toolbox-prod bash -c "
set -eo pipefail
export PATH=/home/azureuser/.local/bin:\$PATH
cd /home/azureuser/toolbox
uv venv
source .venv/bin/activate
uv pip install -e . || true
"
echo 'killing'

set +e pipefail

ssh toolbox-prod <<'EOF'
pkill -f notes_mcp
EOF

set -e pipefail
sleep 3

echo 'starting'
ssh toolbox-prod bash -c "
set -eo pipefail
export USE_MOCK_TRANSCRIPTION=False
export WHISPER_SECRET_KEY=$WHISPER_SECRET_KEY
cd /home/azureuser/toolbox
source .venv/bin/activate
nohup python notes_mcp/app.py > output.log 2>&1 &
"

sleep 1
ssh toolbox-prod "
tail -f /home/azureuser/toolbox/output.log
"
