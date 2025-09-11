import { defineStore } from "pinia";

export const useListsStore = defineStore("lists", {
  state: () => ({
    currentListId: 1,
    currentView: "feed",
    lists: [
      {
        id: 1,
        name: "Vibe coding",
        itemCount: 23,
      },
      {
        id: 2,
        name: "LLM releases",
        itemCount: 18,
      },
      {
        id: 3,
        name: "RAG",
        itemCount: 15,
      },
      {
        id: 4,
        name: "Frontier AI lab capabilities",
        itemCount: 31,
      },
    ],
    listData: {
      1: {
        tweets: [
          {
            id: 1,
            type: "tweet",
            content:
              "Just spent the weekend building a retro terminal emulator in Rust. There's something magical about the green text on black background aesthetic 💚",
            author: {
              name: "RetroCode",
              handle: "@retrocode_dev",
            },
            likes: 342,
            reactions: 89,
            timestamp: "3h",
          },
          {
            id: 2,
            type: "tweet",
            content:
              "Late night coding session with some lo-fi beats. Working on a neural style transfer app that turns your code into ASCII art. The vibes are immaculate ✨",
            author: {
              name: "VibesCoder",
              handle: "@vibes_coder",
            },
            likes: 156,
            reactions: 43,
            timestamp: "6h",
          },
          {
            id: 3,
            type: "tweet",
            content:
              "Nothing beats the satisfaction of refactoring legacy code while listening to synthwave. Clean code + aesthetic vibes = peak developer experience",
            author: {
              name: "SynthDev",
              handle: "@synthwave_dev",
            },
            likes: 278,
            reactions: 67,
            timestamp: "9h",
          },
          {
            id: 4,
            type: "tweet",
            content:
              'Built a mood-based code editor that changes themes based on your Spotify playlist. Currently debugging in "Cyberpunk 2077" mode 🌃',
            author: {
              name: "MoodCode",
              handle: "@moodcode_hq",
            },
            likes: 423,
            reactions: 112,
            timestamp: "12h",
          },
        ],
        summary:
          "The vibe coding community is focused on creating aesthetically pleasing development experiences that combine coding with music, visual themes, and nostalgic elements. Key trends include retro terminal aesthetics, synthwave-inspired development environments, and tools that integrate mood and music into the coding workflow.",
      },
      2: {
        tweets: [
          {
            id: 5,
            type: "tweet",
            content:
              "OpenAI just dropped GPT-4.5 Turbo with 200K context window and 40% faster inference. The multi-modal capabilities are insane! 🚀",
            author: {
              name: "AI News Hub",
              handle: "@ainews_hub",
            },
            likes: 892,
            reactions: 234,
            timestamp: "2h",
          },
          {
            id: 6,
            type: "tweet",
            content:
              "Anthropic's Claude 3.5 Sonnet now supports real-time conversation and can maintain context across 1M+ tokens. Game changer for long-form content.",
            author: {
              name: "ML Updates",
              handle: "@ml_updates",
            },
            likes: 567,
            reactions: 143,
            timestamp: "5h",
          },
          {
            id: 7,
            type: "tweet",
            content:
              "Meta released Code Llama 3 70B - beats GPT-4 on HumanEval benchmark. Open source is catching up fast to proprietary models!",
            author: {
              name: "OpenAI Research",
              handle: "@openai_research",
            },
            likes: 734,
            reactions: 189,
            timestamp: "8h",
          },
          {
            id: 8,
            type: "tweet",
            content:
              "Google's Gemini Ultra 1.5 with native multimodal training is now available via API. Video understanding capabilities are incredible.",
            author: {
              name: "DeepMind Updates",
              handle: "@deepmind_news",
            },
            likes: 445,
            reactions: 98,
            timestamp: "11h",
          },
        ],
        summary:
          "Latest LLM releases show significant advances in context length, multimodal capabilities, and specialized coding performance. OpenAI, Anthropic, Meta, and Google are pushing boundaries with larger context windows, faster inference, and improved reasoning across text, code, and visual inputs.",
      },
      3: {
        tweets: [
          {
            id: 9,
            type: "tweet",
            content:
              "New paper on RAG with knowledge graphs achieves 94% accuracy on complex multi-hop questions. The future of information retrieval is here!",
            author: {
              name: "RAG Research",
              handle: "@rag_research",
            },
            likes: 234,
            reactions: 67,
            timestamp: "4h",
          },
          {
            id: 10,
            type: "tweet",
            content:
              "Just implemented hybrid RAG with vector + keyword search. The semantic understanding combined with exact matching is powerful 🔍",
            author: {
              name: "Search Engineer",
              handle: "@search_eng",
            },
            likes: 189,
            reactions: 45,
            timestamp: "7h",
          },
          {
            id: 11,
            type: "tweet",
            content:
              "ChromaDB + LangChain integration makes building RAG pipelines so much easier. Deployed a knowledge base chatbot in under 100 lines of code.",
            author: {
              name: "LangChain Dev",
              handle: "@langchain_dev",
            },
            likes: 356,
            reactions: 89,
            timestamp: "10h",
          },
          {
            id: 12,
            type: "tweet",
            content:
              "Advanced RAG techniques: query decomposition, document reranking, and answer synthesis. Each step improves retrieval quality significantly.",
            author: {
              name: "Vector DB Pro",
              handle: "@vectordb_pro",
            },
            likes: 278,
            reactions: 73,
            timestamp: "13h",
          },
        ],
        summary:
          "RAG (Retrieval-Augmented Generation) development focuses on improving accuracy through hybrid search methods, knowledge graph integration, and advanced query processing. The community is building sophisticated pipelines that combine semantic and keyword search with multi-step reasoning for complex question answering.",
      },
      4: {
        tweets: [
          {
            id: 13,
            type: "tweet",
            content:
              "OpenAI o1 achieved breakthrough performance on mathematics and coding benchmarks, showing emergent reasoning capabilities we haven't seen before.",
            author: {
              name: "AGI Research",
              handle: "@agi_research",
            },
            likes: 1247,
            reactions: 389,
            timestamp: "1h",
          },
          {
            id: 14,
            type: "tweet",
            content:
              "DeepMind's AlphaCode 3 can now solve competitive programming problems at the level of top human programmers. Code generation has reached new heights.",
            author: {
              name: "Frontier AI Lab",
              handle: "@frontier_ai",
            },
            likes: 892,
            reactions: 234,
            timestamp: "4h",
          },
          {
            id: 15,
            type: "tweet",
            content:
              "Anthropic's Constitutional AI shows how we can align powerful models with human values while maintaining capabilities. Safety + performance.",
            author: {
              name: "AI Safety News",
              handle: "@ai_safety_news",
            },
            likes: 567,
            reactions: 156,
            timestamp: "7h",
          },
          {
            id: 16,
            type: "tweet",
            content:
              "Multi-agent systems are emerging as the next frontier. Claude, GPT-4, and Gemini working together solve problems none could handle alone.",
            author: {
              name: "Multi-Agent AI",
              handle: "@multiagent_ai",
            },
            likes: 734,
            reactions: 198,
            timestamp: "10h",
          },
          {
            id: 17,
            type: "tweet",
            content:
              "New scaling laws suggest we're approaching human-level performance across most cognitive tasks. The capability explosion is accelerating.",
            author: {
              name: "Scaling Laws",
              handle: "@scaling_laws",
            },
            likes: 923,
            reactions: 267,
            timestamp: "13h",
          },
        ],
        summary:
          "Frontier AI labs are achieving breakthrough capabilities in mathematical reasoning, code generation, and multi-agent collaboration. Key developments include emergent reasoning in large models, human-level performance on complex tasks, and successful alignment techniques that maintain both safety and capability advancement.",
      },
    },
    mockSummary:
      "Recent discussions in AI focus on breakthrough developments in reasoning capabilities and the importance of human-AI collaboration. Key themes include open source democratization of ML tools and efficiency improvements in natural language processing. The community emphasizes building augmentative rather than replacement systems.",
  }),

  getters: {
    currentList: (state) =>
      state.lists.find((list) => list.id === state.currentListId),
    currentListItems: (state) =>
      state.listData[state.currentListId]?.tweets || [],
    currentListSummary: (state) =>
      state.listData[state.currentListId]?.summary || state.mockSummary,
  },

  actions: {
    setCurrentList(listId) {
      this.currentListId = listId;
    },

    setCurrentView(view) {
      this.currentView = view;
    },

    async generateSummary() {
      // Mock API call - replace with real API later
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(this.mockSummary);
        }, 1000);
      });
    },

    showAddList() {
      // This will be handled in the component
    },
  },
});
