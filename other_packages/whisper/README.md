# Deploy

```
scp -r ./* nsai-aggregator-gpu:/home/azureuser/whisper
nohup python whisper/app.py > out.log 2>&1 &
```
