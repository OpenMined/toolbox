
# Caveman deploy

```
zip -r - .  -x "**.venv/*" -x ".git/*" -x "data/*" | ssh toolbox-prod "cat > /home/azureuser/archive.zip && rm /home/azureuser.archive.zip && rm -rf /home/azureuser/agentic-syftbox && unzip /home/azureuser/archive.zip -d /home/azureuser/agentic-syftbox"
```

```
ssh toolbox-prod
```

on server
```
cd agentic-syftbox
uv venv
source .venv/bin/activate
cd packages/notes_mcp
uv pip install -e .
nohup python notes_mcp/app.py > output.log 2>&1 &
```
