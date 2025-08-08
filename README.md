<p align="center">
<img alt="Hugging Face Transformers Library" src="https://raw.githubusercontent.com/OpenMined/toolbox/refs/heads/main/packages/toolbox/assets/ToolBox.svg" width="352" height="59" style="max-width: 100%;">
  <br/>
  <br/>
</p>

<p align="center"><b>A privacy-first tool to install mcp servers and background agents for your personal data</b></p>

# Toolbox
Toolbox is a cli tool for installing and managing [MCP](https://github.com/modelcontextprotocol/python-sdk) servers and background agents, made for developers.

- Toolbox aims to support popular developer tools (think github, slack, discord, gmail etc.), and clients (claude desktop, cursor), making it easier to deploy useful MCP servers  
- With toolbox you can install **mcp servers**, **background agents** and their dependencies using the `toolbox install <appname>` command
- **mcp servers** are servers that provide context for LLMs in a standardized way, mostly used for tool calling
- **background agents** are long running processes that create new data based on your existing data (think [RAG](https://en.wikipedia.org/wiki/Retrieval-augmented_generation), [OCR](https://en.wikipedia.org/wiki/Optical_character_recognition),[speech recognition](https://en.wikipedia.org/wiki/Speech_recognition))
- we provide the option to run some of these agents/mcp server in the cloud for free, with the medium term vision of deploying  those components in [trusted execution environments](https://en.wikipedia.org/wiki/Trusted_execution_environment). The first beta versions wont have trusted execution environments, but we wont store any sensitive user data (only meta data). In the long term we plan to make these available at break-even cost (OpenMined is non-profit so we wont make money)



# Install
```
uv pip install -e .
```

## Installation troubleshooting
For CLang issues during installation please run
```
uv python install --reinstall
```
to [fix python in uv](https://github.com/astral-sh/python-build-standalone/pull/414)

You can also try, if `#include <string>` fails
```
CXXFLAGS="-isystem $(xcrun --show-sdk-path)/usr/include/c++/v1" uv pip install -e .
```


# Alpha example

```
tb install slack-mcp
```

# Toolbox CLI
To show apps in store
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
To get logs for a local app (to follow add -f)
```
tb log <appname>
```


# Store

| Name | Clients | Default Deployment | Read Access | Write Access | Install |
|------|--------|--------------------|-------------|--------------|---------|
| github-mcp | claude | stdio | Issues, PRs, Settings | Issues, PRs, Settings | `tb install github-mcp` |
| meeting-notes-mcp | claude | proxy-to-om-enclave | Apple Audio Recordings | Meeting Notes | `tb install meeting-notes-mcp` |
| whatsapp-desktop-mcp | claude | proxy-to-om-enclave | WhatsApp Messages | WhatsApp Messages | `tb install whatsapp-desktop-mcp` |
| slack-mcp | claude | proxy-to-om-enclave | Slack Messages | Slack Messages | `tb install slack-mcp` |


# Triggers

Toolbox can run scripts on a schedule to automate tasks in your MCP pipeline. See the [triggers documentation](docs/triggers.md) for setup and usage instructions.




# Troubleshooting screenpipe
If you dont seen audio recordings under `tb show meeting-notes-mcp`. The following things may help

- make sure you gave screenpipe the right permissions for recording video and audio in under Privacy and security (screenpipe should automatically request this). 
- Also make sure you select the right audio device by clicking -> person icon in the right top -> settings -> recording -> audio devices -> and then select the right one. 
- By default screenpipe uses local trancription, which we are not using because it might be heavy on your laptop. However, screenpipe will still try to download the model, which may block transcription. To prevent this, choose a small model like `whisper-tiny-quantized` under -> person icon in the right top -> settings -> recording -> audio-transcription-model


