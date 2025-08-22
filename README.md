<p align="center">
<img alt="Hugging Face Transformers Library" src="https://raw.githubusercontent.com/OpenMined/toolbox/refs/heads/main/packages/toolbox/assets/ToolBox.svg" width="352" height="59" style="max-width: 100%;">
  <br/>
  <br/>
</p>

<p align="center"><b>A privacy-first tool to install mcp servers and background agents for your personal data</b></p>

# Toolbox

Toolbox is a cli tool for installing and managing [MCP](https://github.com/modelcontextprotocol/python-sdk) servers and background agents, **made for developers**.

- Toolbox supports popular developer tools (think github, slack, discord, obsidian, gmail etc.), and clients (claude desktop, cursor), making it easier to deploy useful MCP servers without having them managed by a specific client
- With toolbox you can install **mcp servers** with **background agents** and their dependencies using
  `toolbox install <appname>`
- background agents download your data or index it (OCR/transcription/embeddings for RAG); you can choose between fully local or free hosted in [openmined enclaves](#hosted-option-with-enclaves)

## TOC

- [Use cases](#use-cases)
- [Installation](#install)
- [CLI](#toolbox-cli)
- [Store](#store)
- [Enclaves](#hosted-option-with-enclaves)

## Use cases

- 🧠🔎 Customizable, Custom Topic Tracking (Discord, Whatsapp, Github, Slack) Follow technical topics across multiple Discord servers (or other sources) with periodic, fully customizable summaries. Tailor what you want to see using simple prompt files — get only the updates that matter, automatically and efficiently.
- 📋⚡ One-Command Ticket Creation (Obsidian, Github) — Turn your Obsidian TODOs into GitHub issues with a single command: no copy-pasting, no clicking, just seamless ticket creation directly from your notes.
- 🔔✨ LLM-driven custom notifications (Slack, Discord, Whatsapp) Use simple prompts or code to write instructions to decide when a message deserves a reminder (forgot to respond, missed a todo, etc)
- 📊🪄 Organize your communication for Projects or Campaigns (Slack, Discord, Google Sheets, Google Calendar) Log every person you’ve reached out to around a certain topic into a Google Sheet, complete with date, calendar events and status

## Requirements

Before installing toolbox, make sure you have the following:

- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Install

To install toolbox on your machine from PyPI, you can use `uv tool`:

```
uv tool install --prerelease allow --python 3.12 -U syft-toolbox
# to verify installation
tb info
```

Alternatively, you can install toolbox from source, using `uv`:

```
git clone https://github.com/OpenMined/toolbox.git
cd toolbox
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

## Alpha example

```
tb install slack-mcp
```

## Toolbox CLI

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

## Store

| Name                 | Clients | Default Deployment  | Read Access            | Write Access          | Install                           |
| -------------------- | ------- | ------------------- | ---------------------- | --------------------- | --------------------------------- |
| slack-mcp            | claude  | proxy-to-om-enclave | Slack Messages         | Slack Messages        | `tb install slack-mcp`            |
| discord-mcp          | claude  | proxy-to-om-enclave | Discord Messages       | Discord Messages      | `tb install slack-mcp`            |
| obsidian-mcp         | claude  | proxy-to-om-enclave | Obsidian notes         | Obsidian Notes        | `tb install obsidian-mcp`         |
| github-mcp           | claude  | stdio               | Issues, PRs, Settings  | Issues, PRs, Settings | `tb install github-mcp`           |
| whatsapp-desktop-mcp | claude  | proxy-to-om-enclave | WhatsApp Messages      | WhatsApp Messages     | `tb install whatsapp-desktop-mcp` |
| pdf-mcp              | claude  | proxy-to-om-enclave | Local Documents        | Document Embeddings   | `tb install pdf-mcp`              |
| meeting-notes-mcp    | claude  | proxy-to-om-enclave | Apple Audio Recordings | Meeting Notes         | `tb install meeting-notes-mcp`    |

# Triggers

Toolbox can run scripts on a schedule to automate tasks in your MCP pipeline. See the [triggers documentation](docs/triggers.md) for setup and usage instructions.

## Troubleshooting screenpipe

If you dont seen audio recordings under `tb show meeting-notes-mcp`. The following things may help

- make sure you gave screenpipe the right permissions for recording video and audio in under Privacy and security (screenpipe should automatically request this).
- Also make sure you select the right audio device by clicking -> person icon in the right top -> settings -> recording -> audio devices -> and then select the right one.
- By default screenpipe uses local trancription, which we are not using because it might be heavy on your laptop. However, screenpipe will still try to download the model, which may block transcription. To prevent this, choose a small model like `whisper-tiny-quantized` under -> person icon in the right top -> settings -> recording -> audio-transcription-model

## Analytics

We collect anonymous analytics to understand how the cli is used. The data we track includes:

- **Command usage**: Which CLI commands are run (install, list, list-store, reset)
- **Command parameters**: Non-sensitive command arguments (app names, flags like --use-local-deployments)
- **Toolbox version**: The version of toolbox being used
- **Error information**: If commands fail, we log the error type and message for debugging
- **Anonymous user ID**: A randomly generated UUID stored locally to understand usage patterns across multiple CLI commands

To opt out, run `tb setup` and disable analytics.

## Hosted option with enclaves

we provide the option to run some of these agents/mcp server in the cloud for free, with the medium term vision of deploying those components in [trusted execution environments](https://en.wikipedia.org/wiki/Trusted_execution_environment). The first beta versions wont have trusted execution environments, but we wont store any sensitive user data (only meta data). In the long term we plan to make these available at break-even cost (OpenMined is non-profit so we wont make money)
