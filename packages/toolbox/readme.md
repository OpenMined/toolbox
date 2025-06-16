

# Install
```
uv pip install -e .
```

# Installing apps
To list installed apps
```
tb list
``` 
To install a new app
```
tb install <app_name>
```


# Store


| Name | Clients | Default Deployment | Read Access | Write Access | Install |
|------|--------|------------|-------------|--------------|-------|
| github-mcp | claude | stdio | Issues, PRs, Settings | Issues, PRs, Settings | `tb install github-mcp` |
| meeting-notes-mcp | claude | proxy-to-om-enclave | Apple Audio Recordings | Meeting Notes | `tb install meeting-notes-mcp` |
| screen-recording-mcp | claude | app | Apple-mic-input, Apple-video-input | Apple Audio Recordings, Apple Video Recordings |  |

