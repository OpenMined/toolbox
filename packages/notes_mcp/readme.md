
# Caveman deploy

```
zip -r - .  -x "**.venv/*" -x ".git/*" -x "data/*" | ssh toolbox-prod "cat > /home/azureuser/archive.zip && rm -rf /home/azureuser/toolbox && unzip /home/azureuser/archive.zip -d /home/azureuser/toolbox"
```

```
ssh toolbox-prod
```

on server
```
cd /home/azureuser/toolbox
uv venv
source .venv/bin/activate
uv pip install -e .
pkill -f notes_mcp
sleep 3
nohup python notes_mcp/app.py > output.log 2>&1 &
```
