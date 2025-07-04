<p align="center">
<img alt="Hugging Face Transformers Library" src="https://raw.githubusercontent.com/OpenMined/agentic-syftbox/refs/heads/main/packages/toolbox/assets/ToolBox.svg" width="352" height="59" style="max-width: 100%;">
  <br/>
  <br/>
</p>

<p align="center"><b>A privacy-first tool to install mcp servers and background agents for your personal data</b></p>

# Toolbox
Toolbox is a cli tool for installing and managing [MCP](https://github.com/modelcontextprotocol/python-sdk) servers and background agents, made for developers.

- Toolbox aims to support popular developer tools (think github, slack, discord, gmail etc.), and clients (claude desktop, cursor), making it easier to deploy useful MCP servers  
- With toolbox you can install **mcp servers** and **background agents** usiong the `toolbox install <appname>` command
- **mcp servers** are servers that provide context for LLMs in a standardized way, mostly used for tool calling
- **background agents** are long running processes that create new data based on your existing data (think [RAG](https://en.wikipedia.org/wiki/Retrieval-augmented_generation), [OCR](https://en.wikipedia.org/wiki/Optical_character_recognition),[speech recognition](https://en.wikipedia.org/wiki/Speech_recognition))
- we provide the option to run some of these agents/mcp server in the cloud, with the medium term vision of deploying  those components in [trusted execution environments](https://en.wikipedia.org/wiki/Trusted_execution_environment). In the first beta versions this wont be supported, but we wont store any sensitive user data (only meta data).



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

