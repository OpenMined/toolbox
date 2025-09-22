#!/bin/zsh

set -eo pipefail


cd /Users/koen/workspace/toolbox/packages/omni
ssh toolbox-prod "rm -rf /home/azureuser/omni"
zip -r - .  -x "**.venv/*" -x ".git/*" -x "data/*" | ssh toolbox-prod "cat > /home/azureuser/archive.zip && rm -rf /home/azureuser/omni && unzip /home/azureuser/archive.zip -d /home/azureuser/omni"


echo 'installing'
ssh toolbox-prod bash -c "
set -eo pipefail
export PATH=/home/azureuser/.local/bin:\$PATH
cd /home/azureuser/omni
uv venv
source .venv/bin/activate
uv pip install -e . || true
npm install
"
echo 'killing'

set +e pipefail

ssh toolbox-prod <<'EOF'
pkill -f omni
pkill -f "npm run dev" || true
pkill -f "python.*app.py" || true
pkill -f "uvicorn.*app:app" || true
EOF

set -e pipefail
sleep 3

echo 'starting'
ssh toolbox-prod bash -c "
set -eo pipefail
export BACKEND_URL=http://20.224.153.50:8002

cd /home/azureuser/omni
source .venv/bin/activate
nohup npm run dev > output_omni_frontend.log 2>&1 &
nohup python omni/app.py > output_omni_backend.log 2>&1 &
"

sleep 1
ssh toolbox-prod "
tail -f /home/azureuser/omni/output_omni_frontend.log
tail -f /home/azureuser/omni/output_omni_backend.log
"
