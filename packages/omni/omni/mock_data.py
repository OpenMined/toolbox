def get_mock_data_sources():
    return [
        {
            "id": "twitter",
            "name": "Twitter",
            "icon": "twitter",
            "description": "Connect your Twitter account to analyze tweets and conversations",
            "installCommand": "toolbox install twitter-mcp",
            "defaultUrl": "localhost:8020",
            "connectionState": "connected",
            "dashboardData": {
                "handle": "@johndoe",
                "totalTweets": 1247,
                "latestTweets": [
                    {
                        "id": 1,
                        "content": "Just discovered an amazing new AI breakthrough in transformer architectures! The potential applications are endless.",
                        "timestamp": "2h ago",
                        "likes": 42,
                        "retweets": 18,
                    },
                    {
                        "id": 2,
                        "content": "Working on some exciting ML projects. The intersection of AI and creativity continues to amaze me every day.",
                        "timestamp": "5h ago",
                        "likes": 28,
                        "retweets": 7,
                    },
                ],
                "embeddingCounts": {
                    "ollama/nomic-embed-text": 123,
                    "openai/text-embedding-3-small": 89,
                },
            },
        },
        {
            "id": "ai-papers",
            "name": "AI Papers",
            "icon": "papers",
            "description": "Connect to AI paper repositories and research databases",
            "installCommand": "toolbox install papers-mcp",
            "defaultUrl": "localhost:8022",
            "connectionState": "connected",
            "dashboardData": {
                "totalPapers": 847,
                "trendingPapers": 156,
                "syftboxPapers": 23,
                "latestPaper": "Jan 15",
                "latestPapers": [
                    {
                        "id": 1,
                        "title": "Attention Is All You Need: Revisiting Transformer Architectures",
                        "summary": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms...",
                        "authors": "Vaswani et al.",
                        "arxivId": "2401.12345",
                        "timestamp": "2h ago",
                    },
                ],
                "embeddingCounts": {
                    "ollama/nomic-embed-text": 234,
                    "openai/text-embedding-3-small": 178,
                },
            },
        },
        {
            "id": "discord",
            "name": "Discord",
            "icon": "discord",
            "description": "Connect Discord servers to analyze messages and conversations",
            "installCommand": "toolbox install discord-mcp",
            "defaultUrl": "localhost:8021",
            "connectionState": "disconnected",
            "dashboardData": {
                "totalServers": 0,
                "totalChannels": 0,
                "totalMessages": 0,
                "embeddingCounts": {},
            },
        },
    ]


def get_mock_data_collections():
    return [
        {"id": "twitter", "name": "Twitter", "items": []},
        {"id": "ai-papers", "name": "AI Papers", "items": []},
        {"id": "discord", "name": "Discord", "items": []},
    ]


def get_mock_smart_lists():
    return [
        {
            "id": 1,
            "name": "Vibe coding",
            "listSources": [
                {
                    "dataSourceId": "twitter",
                    "filters": {
                        "dateRange": {"from": "2025-07-01", "to": "2025-10-01"},
                        "ragQuery": "vibe coding",
                        "threshold": 0.42,
                        "authors": [
                            "@CrazyJvm",
                            "@seb_ruder",
                            "@Devendr06654102",
                            "@weaviate_io",
                            "@PSH_Lewis",
                            "@douwekiela",
                            "@steipete",
                            "@jeremyphoward",
                            "@bobvanluijt",
                        ],
                    },
                }
            ],
            "itemCount": 23,
        },
        {
            "id": 2,
            "name": "LLM releases",
            "listSources": [
                {
                    "dataSourceId": "twitter",
                    "filters": {
                        "dateRange": {"from": "2025-07-01", "to": "2025-10-01"},
                        "ragQuery": "LLM model release",
                        "threshold": 0.43,
                        "authors": [
                            "@CrazyJvm",
                            "@seb_ruder",
                            "@Devendr06654102",
                            "@weaviate_io",
                            "@PSH_Lewis",
                            "@douwekiela",
                            "@steipete",
                            "@jeremyphoward",
                            "@bobvanluijt",
                        ],
                    },
                }
            ],
            "computedItems": [],
            "itemCount": 18,
        },
        {
            "id": 3,
            "name": "RAG",
            "listSources": [
                {
                    "dataSourceId": "twitter",
                    "filters": {
                        "dateRange": {"from": "2025-07-01", "to": "2025-10-01"},
                        "ragQuery": "RAG retrieval augmented generation",
                        "threshold": 0.43,
                        "authors": [
                            "@CrazyJvm",
                            "@seb_ruder",
                            "@Devendr06654102",
                            "@weaviate_io",
                            "@PSH_Lewis",
                            "@douwekiela",
                            "@steipete",
                            "@jeremyphoward",
                            "@bobvanluijt",
                        ],
                    },
                }
            ],
            "computedItems": [],
            "itemCount": 15,
        },
    ]


def get_mock_summary(list_id: int):
    summaries = {
        1: "• Retro aesthetics dominating: terminal emulators, green-on-black themes, and vintage computing vibes [1,3]\n• Music-driven development: lo-fi beats, synthwave soundtracks integrated into coding workflows [2,4]\n• Mood-based tooling: editors that adapt themes to Spotify playlists and emotional states [4]\n• ASCII art and visual programming: neural style transfer turning code into art [2]",
        2: "• Massive context windows: GPT-4.5 Turbo (200K tokens), Claude 3.5 Sonnet (1M+ tokens) [5,6]\n• Multimodal breakthroughs: real-time conversation, video understanding, native training [6,8]\n• Coding excellence: Code Llama 3 70B beating GPT-4 on HumanEval benchmark [7]\n• Speed improvements: 40% faster inference across major model releases [5,8]",
        3: "• Hybrid search dominance: combining vector similarity with keyword matching for better retrieval [10]\n• Knowledge graph integration: 94% accuracy on complex multi-hop questions [9]\n• Simplified tooling: ChromaDB + LangChain enabling sub-100 line implementations [11]\n• Advanced techniques: query decomposition, document reranking, and answer synthesis [12]",
        4: "• Reasoning breakthroughs: OpenAI o1 showing emergent capabilities in mathematics and coding [13]\n• Human-level programming: AlphaCode 3 solving competitive programming at expert level [14]\n• Multi-agent systems: Claude, GPT-4, and Gemini collaborating on complex problems [16]\n• Safety + capability: Constitutional AI aligning powerful models without performance loss [15]",
    }
    return summaries.get(
        list_id,
        "Recent discussions focus on breakthrough developments and the importance of human-AI collaboration.",
    )


def get_mock_chats(list_id: int):
    mock_chats = {
        1: [
            {
                "id": 1,
                "messages": [
                    {
                        "id": 1,
                        "role": "user",
                        "content": "What is the best tool for vibe coding?",
                        "timestamp": "2024-01-15T10:00:00Z",
                    },
                    {
                        "id": 2,
                        "role": "assistant",
                        "content": "Currently, Cursor/windsurf are popular as IDEs, and claude code and codex for CLIs.",
                        "timestamp": "2024-01-15T10:00:30Z",
                    },
                ],
            }
        ]
    }
    return mock_chats.get(list_id, [])
