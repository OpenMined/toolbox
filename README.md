<p align="center">
<img alt="Hugging Face Transformers Library" src="https://raw.githubusercontent.com/OpenMined/agentic-syftbox/refs/heads/main/packages/toolbox/assets/ToolBox.svg" width="352" height="59" style="max-width: 100%;">
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

# Alpha example
This is an alpha version, currently the only functioning app is the meeting-notes-mcp, with the slack-mcp coming soon. The only supported client is Claude Desktop, which is also the default client. Install this app and its dependencies using:
```
tb install meeting-notes-mcp --client=claude
```
After making some recording using screenpipe you should be able to see your data using
```
tb show meeting-notes-mcp
```
This should now show you the nr of audio chunks screenpipe recorded and how many are transcribed. When you start talking they should start appearting within 30 seconds. If not, check [troubleshooting screenpipe](#troubleshooting-screenpipe)

Once you have recordings, you can then query them with Claude desktop by asking something like

**"Get me the meeting notes from my latest meeting"**

## Bonus
If you also install the github mcp server you could also ask

## Troubleshooting screenpipe
If you dont seen audio recordings under `tb show meeting-notes-mcp`. The following things may help

- make sure you gave screenpipe the right permissions for recording video and audio in under Privacy and security (screenpipe should automatically request this). 
- Also make sure you select the right audio device by clicking -> person icon in the right top -> settings -> recording -> audio devices -> and then select the right one. 
- By default screenpipe uses local trancription, which we are not using because it might be heavy on your laptop. However, screenpipe will still try to download the model, which may block transcription. To prevent this, choose a small model like `whisper-tiny-quantized` under -> person icon in the right top -> settings -> recording -> audio-transcription-model

**"Now make tickets for the todo's of that meeting"**


# Installing apps
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
To get logs for a local app
```
tb log <appname>
```

# Store


# Store


| Name | Clients | Default Deployment | Read Access | Write Access | Install |
|------|--------|--------------------|-------------|--------------|---------|
| github-mcp | claude | stdio | Issues, PRs, Settings | Issues, PRs, Settings | `tb install github-mcp` |
| meeting-notes-mcp | claude | proxy-to-om-enclave | Apple Audio Recordings | Meeting Notes | `tb install meeting-notes-mcp` |
| whatsapp-desktop-mcp | claude | proxy-to-om-enclave | WhatsApp Messages | WhatsApp Messages | `tb install whatsapp-desktop-mcp` |
| slack-mcp | claude | proxy-to-om-enclave | Slack Messages | Slack Messages | `tb install slack-mcp` |

