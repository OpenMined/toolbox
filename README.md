<p align="center">
<img alt="Hugging Face Transformers Library" src="https://raw.githubusercontent.com/OpenMined/agentic-syftbox/refs/heads/main/packages/toolbox/assets/ToolBox.svg" width="352" height="59" style="max-width: 100%;">
  <br/>
  <br/>
</p>

<p align="center"><b>A privacy-first tool to install local and remote mcp servers for your personal data</b></p>

# Install
```
uv pip install -e .
```

# Installing apps
To shwo apps in store
```
tb list-store
```
To list installed apps
```
tb list
``` 
To install a new app
```
tb install <app_name>
```
To show an installed app
```
tb show <appname>
```
To get logs for a local app
```
tb log <appname>
```

# Example
tb install meeting-notes-mcp


# Store


| Name | Clients | Default Deployment | Read Access | Write Access | Install |
|------|--------|------------|-------------|--------------|-------|
| github-mcp | claude | stdio | Issues, PRs, Settings | Issues, PRs, Settings | `tb install github-mcp` |
| meeting-notes-mcp | claude | proxy-to-om-enclave | Apple Audio Recordings | Meeting Notes | `tb install meeting-notes-mcp` |
| screen-recording-syncer | claude | proxy-to-local | Apple Audio Recordings | Apple Audio Recordings over syftbox | `tb install screen-recording-syncer` |
| screen-recording-mcp | claude | app | Apple-mic-input, Apple-video-input | Apple Audio Recordings, Apple Video Recordings | `tb install screen-recording-mcp`|

