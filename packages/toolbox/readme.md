<p align="center">
<img alt="Hugging Face Transformers Library" src="https://raw.githubusercontent.com/OpenMined/toolbox/refs/heads/main/packages/toolbox/assets/ToolBox.svg" width="352" height="59" style="max-width: 100%;">
  <br/>
  <br/>
</p>

<p align="center"><b>A privacy-first tool to install local and remote mcp servers for your personal data</b></p>

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
tb install <app_name> --client="claude"
```

# Example

```
tb install meeting-notes-mcp
```

# Store

| Name                 | Clients | Default Deployment  | Read Access            | Write Access          | Install                           |
| -------------------- | ------- | ------------------- | ---------------------- | --------------------- | --------------------------------- |
| github-mcp           | claude  | stdio               | Issues, PRs, Settings  | Issues, PRs, Settings | `tb install github-mcp`           |
| meeting-notes-mcp    | claude  | proxy-to-om-enclave | Apple Audio Recordings | Meeting Notes         | `tb install meeting-notes-mcp`    |
| whatsapp-desktop-mcp | claude  | proxy-to-om-enclave | WhatsApp Messages      | WhatsApp Messages     | `tb install whatsapp-desktop-mcp` |
| slack-mcp            | claude  | proxy-to-om-enclave | Slack Messages         | Slack Messages        | `tb install slack-mcp`            |
