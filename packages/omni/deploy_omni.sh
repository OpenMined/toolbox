#!/bin/zsh

set -eo pipefail

TOOLBOX_DIR="${TOOLBOX_DIR:-/Users/koen/workspace/toolbox}"

echo "Deploying from $TOOLBOX_DIR/packages/omni to toolbox-prod"

cd "$TOOLBOX_DIR/packages/omni"
ssh toolbox-prod "rm -rf /home/azureuser/omni"
zip -r - .  -x "**.venv/*" -x ".git/*" -x "data/*" -x "node_modules/*" | ssh toolbox-prod "cat > /home/azureuser/archive.zip && rm -rf /home/azureuser/omni && unzip /home/azureuser/archive.zip -d /home/azureuser/omni"



echo 'installing'
ssh toolbox-prod /bin/bash -c "
set -eo pipefail
export PATH=/home/azureuser/.local/bin:/home/azureuser/.nvm/versions/node/v20.19.5/bin:\$PATH
cd /home/azureuser/omni
uv venv
source .venv/bin/activate
# uv cache clean
uv pip install --refresh --prerelease allow -e . || true
npm install
npm install -g serve
"
echo 'killing'

set +e pipefail

ssh toolbox-prod <<'EOF'
pkill -f omni
pkill -f "npm run build" || true
pkill -f "python.*app.py" || true
pkill -f "uvicorn.*app:app" || true
EOF

set -e pipefail
sleep 3

echo 'starting'
ssh toolbox-prod bash -c "
set -eo pipefail
export PATH=/home/azureuser/.local/bin:/home/azureuser/.nvm/versions/node/v20.19.5/bin:\$PATH
export VITE_API_BASE_URL=http://20.224.153.50:8000
export USE_ANTHROPIC=True
export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

cd /home/azureuser/omni
source .venv/bin/activate

npm run build
nohup serve -s dist -l 8005 > output_omni_frontend.log 2>&1 &
nohup python omni/app.py > output_omni_backend.log 2>&1 &
"

sleep 1
ssh toolbox-prod "
tail -f /home/azureuser/omni/output_omni_backend.log /home/azureuser/omni/output_omni_frontend.log
"
