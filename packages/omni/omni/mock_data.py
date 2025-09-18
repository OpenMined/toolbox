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
                        "dateRange": {"from": "2025-07-01", "to": "2025-12-31"},
                        "ragQuery": "coding aesthetics vibes music",
                        "threshold": 0.6,
                    },
                }
            ],
            "computedItems": [],
            "itemCount": 23,
        },
        {
            "id": 2,
            "name": "LLM releases",
            "listSources": [
                {
                    "dataSourceId": "twitter",
                    "filters": {
                        "dateRange": {"from": "2025-07-01", "to": "2025-12-31"},
                        "ragQuery": "LLM releases GPT Claude models",
                        "threshold": 0.6,
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
                        "threshold": 0.4,
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
                            "@rohanpaul_ai",
                        ],
                    },
                }
            ],
            "computedItems": [],
            "itemCount": 15,
        },
        {
            "id": 4,
            "name": "Frontier AI lab capabilities",
            "listSources": [
                {
                    "dataSourceId": "twitter",
                    "filters": {
                        "dateRange": {"from": "2025-07-01", "to": "2025-12-31"},
                        "ragQuery": "AGI research breakthrough capabilities reasoning",
                        "threshold": 0.5,
                    },
                }
            ],
            "computedItems": [],
            "itemCount": 31,
        },
    ]


def get_mock_smart_list_items(list_id: int):
    mock_data = {
        1: [
            {
                "id": 1,
                "type": "tweet",
                "content": "Just spent the weekend building a retro terminal emulator in Rust. There's something magical about the green text on black background aesthetic 💚",
                "author": {
                    "name": "RetroCode",
                    "handle": "@retrocode_dev",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1588180280910397440/hP8GtFeC_400x400.jpg",
                },
                "likes": 342,
                "reactions": 89,
                "timestamp": "3h",
            },
            {
                "id": 2,
                "type": "tweet",
                "content": "Late night coding session with some lo-fi beats. Working on a neural style transfer app that turns your code into ASCII art. The vibes are immaculate ✨",
                "author": {
                    "name": "VibesCoder",
                    "handle": "@vibes_coder",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1584508555726422017/LJjmzFgD_400x400.jpg",
                },
                "likes": 156,
                "reactions": 43,
                "timestamp": "6h",
            },
            {
                "id": 3,
                "type": "tweet",
                "content": "Nothing beats the satisfaction of refactoring legacy code while listening to synthwave. Clean code + aesthetic vibes = peak developer experience",
                "author": {
                    "name": "SynthDev",
                    "handle": "@synthwave_dev",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1579552280645206016/b2rfCHOe_400x400.jpg",
                },
                "likes": 278,
                "reactions": 67,
                "timestamp": "9h",
            },
            {
                "id": 4,
                "type": "tweet",
                "content": 'Built a mood-based code editor that changes themes based on your Spotify playlist. Currently debugging in "Cyberpunk 2077" mode 🌃',
                "author": {
                    "name": "MoodCode",
                    "handle": "@moodcode_hq",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1582796999012077568/lXK8S7nG_400x400.jpg",
                },
                "likes": 423,
                "reactions": 112,
                "timestamp": "12h",
            },
        ],
        2: [
            {
                "id": 5,
                "type": "tweet",
                "content": "OpenAI just dropped GPT-4.5 Turbo with 200K context window and 40% faster inference. The multi-modal capabilities are insane! 🚀",
                "author": {
                    "name": "AI News Hub",
                    "handle": "@ainews_hub",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1590834832027918337/6qF4hYnJ_400x400.jpg",
                },
                "likes": 892,
                "reactions": 234,
                "timestamp": "2h",
            },
            {
                "id": 6,
                "type": "tweet",
                "content": "Anthropic's Claude 3.5 Sonnet now supports real-time conversation and can maintain context across 1M+ tokens. Game changer for long-form content.",
                "author": {
                    "name": "ML Updates",
                    "handle": "@ml_updates",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1587456789456789456/abcd1234_400x400.jpg",
                },
                "likes": 567,
                "reactions": 143,
                "timestamp": "5h",
            },
            {
                "id": 7,
                "type": "tweet",
                "content": "Meta released Code Llama 3 70B - beats GPT-4 on HumanEval benchmark. Open source is catching up fast to proprietary models!",
                "author": {
                    "name": "OpenAI Research",
                    "handle": "@openai_research",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1634058036934500352/b4F1eVpJ_400x400.jpg",
                },
                "likes": 734,
                "reactions": 189,
                "timestamp": "8h",
            },
            {
                "id": 8,
                "type": "tweet",
                "content": "Google's Gemini Ultra 1.5 with native multimodal training is now available via API. Video understanding capabilities are incredible.",
                "author": {
                    "name": "DeepMind Updates",
                    "handle": "@deepmind_news",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1543897644427907075/QNyb85yY_400x400.jpg",
                },
                "likes": 445,
                "reactions": 98,
                "timestamp": "11h",
            },
        ],
        3: [
            {
                "id": 9,
                "type": "tweet",
                "content": "New paper on RAG with knowledge graphs achieves 94% accuracy on complex multi-hop questions. The future of information retrieval is here!",
                "author": {
                    "name": "RAG Research",
                    "handle": "@rag_research",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1589123456789012345/xyz12345_400x400.jpg",
                },
                "likes": 234,
                "reactions": 67,
                "timestamp": "4h",
            },
            {
                "id": 10,
                "type": "tweet",
                "content": "Just implemented hybrid RAG with vector + keyword search. The semantic understanding combined with exact matching is powerful 🔍",
                "author": {
                    "name": "Search Engineer",
                    "handle": "@search_eng",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1582456789123456789/searcheng_400x400.jpg",
                },
                "likes": 189,
                "reactions": 45,
                "timestamp": "7h",
            },
            {
                "id": 11,
                "type": "tweet",
                "content": "ChromaDB + LangChain integration makes building RAG pipelines so much easier. Deployed a knowledge base chatbot in under 100 lines of code.",
                "author": {
                    "name": "LangChain Dev",
                    "handle": "@langchain_dev",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1576297983333912576/CgsRFpdo_400x400.jpg",
                },
                "likes": 356,
                "reactions": 89,
                "timestamp": "10h",
            },
            {
                "id": 12,
                "type": "tweet",
                "content": "Advanced RAG techniques: query decomposition, document reranking, and answer synthesis. Each step improves retrieval quality significantly.",
                "author": {
                    "name": "Vector DB Pro",
                    "handle": "@vectordb_pro",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1583789456123456789/vectordb_400x400.jpg",
                },
                "likes": 278,
                "reactions": 73,
                "timestamp": "13h",
            },
        ],
        4: [
            {
                "id": 13,
                "type": "tweet",
                "content": "OpenAI o1 achieved breakthrough performance on mathematics and coding benchmarks, showing emergent reasoning capabilities we haven't seen before.",
                "author": {
                    "name": "AGI Research",
                    "handle": "@agi_research",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1591234567891234567/agiresrch_400x400.jpg",
                },
                "likes": 1247,
                "reactions": 389,
                "timestamp": "1h",
            },
            {
                "id": 14,
                "type": "tweet",
                "content": "DeepMind's AlphaCode 3 can now solve competitive programming problems at the level of top human programmers. Code generation has reached new heights.",
                "author": {
                    "name": "Frontier AI Lab",
                    "handle": "@frontier_ai",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1586456789012345678/frontier_400x400.jpg",
                },
                "likes": 892,
                "reactions": 234,
                "timestamp": "4h",
            },
            {
                "id": 15,
                "type": "tweet",
                "content": "Anthropic's Constitutional AI shows how we can align powerful models with human values while maintaining capabilities. Safety + performance.",
                "author": {
                    "name": "AI Safety News",
                    "handle": "@ai_safety_news",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1580987654321098765/aisafety_400x400.jpg",
                },
                "likes": 567,
                "reactions": 156,
                "timestamp": "7h",
            },
            {
                "id": 16,
                "type": "tweet",
                "content": "Multi-agent systems are emerging as the next frontier. Claude, GPT-4, and Gemini working together solve problems none could handle alone.",
                "author": {
                    "name": "Multi-Agent AI",
                    "handle": "@multiagent_ai",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1585432109876543210/multiagnt_400x400.jpg",
                },
                "likes": 734,
                "reactions": 198,
                "timestamp": "10h",
            },
            {
                "id": 17,
                "type": "tweet",
                "content": "New scaling laws suggest we're approaching human-level performance across most cognitive tasks. The capability explosion is accelerating.",
                "author": {
                    "name": "Scaling Laws",
                    "handle": "@scaling_laws",
                    "avatarUrl": "https://pbs.twimg.com/profile_images/1592345678901234567/scaling_400x400.jpg",
                },
                "likes": 923,
                "reactions": 267,
                "timestamp": "13h",
            },
        ],
    }
    return mock_data.get(list_id, [])


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
                        "content": "What music do developers prefer while coding?",
                        "timestamp": "2024-01-15T10:00:00Z",
                    },
                    {
                        "id": 2,
                        "role": "assistant",
                        "content": "Based on the tweets, developers favor lo-fi beats, synthwave, and atmospheric music that creates an immersive coding environment.",
                        "timestamp": "2024-01-15T10:00:30Z",
                    },
                ],
            }
        ]
    }
    return mock_chats.get(list_id, [])
