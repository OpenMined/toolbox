# Toolbox store - SQLite MVP

## Overview

We're building a local-first application that enables intelligent querying across personal data sources using semantic search, traditional filtering, and hybrid queries. Users can index their own data and perform complex searches without relying on cloud services.

## Technical Architecture

### Technology:

- new package `toolbox_store`, for both ingestion and querying
  - (P2) FastAPI app/router for http api
  - (P2) CLI for claude code integration
- SQLite with sqlite-vec and FTS5 extensions
  - This will be fine for MVP and smaller datasets (<100k rows)
  - If larger is needed, we probably need to switch to a vector db (like Lance,qdrant), but this makes it more complex
    - example: need more complex pre/post filtering logic to coordinate semantic queries and filtering between 2 db's
- JSON metadata for flexible storage of different data sources
  - If more performance is needed, we can move to different schema in later version

### Database Schema

```sql
CREATE TABLE obsidian_documents (
    id TEXT PRIMARY KEY,       -- UUID by default, custom string (e.g. external ID) if needed
    metadata JSON,             -- Metadata is schemaless
    source TEXT,               -- 'whatsapp', 'slack', 'file:///path/to/file.pdf', 'syft://path/to/file'
    content TEXT               -- not nullable for now, e.g. could contain cleaned up OCR text from a PDF
);

CREATE TABLE obsidian_embeddings (
    document_id TEXT REFERENCES obsidian_documents(id),
    chunk_index INTEGER,
    indexed_at DATETIME,
    content TEXT,
    chunk_start INTEGER,
    chunk_end INTEGER,
    content_hash TEXT,
    embedding VECTOR,
    PRIMARY KEY (document_id, chunk_index)
);
```

**Collection Names:** Table names are prefixed with collection name (e.g., `obsidian_`, `slack_`, `zotero_`) to support multiple vector stores in the same database (eg for versioning or different data sources).

### Query Interface

```python
# Semantic search
results = store.search(collection="obsidian").semantic("machine learning algorithms").to_list()

# Traditional filtering
results = store.search(collection="slack").filter({
    'metadata.source': 'slack',
    'metadata.sender': 'john',
    'metadata.timestamp__gte': '2024-09-01'
}).to_pydantic(model=Document)

# Hybrid queries
# Equal weighting (default)
results = store.search(collection="zotero")
    .keyword("budget discussion")
    .semantic("financial planning meeting")
    .to_pandas()

# Custom weighting + filters
results = store.search(collection="zotero")
    .keyword("budget discussion")
    .semantic("financial planning meeting")
    .hybrid(method="linear", keyword_weight=0.3)  # 0.3 * keyword + 0.7 * semantic weight
    .filter({'metadata.timestamp__gte': '2024-08-01'})
    .to_pandas()
```

**Filter Syntax:**

- Django-style operators: `__gte`, `__lt`, `__in`, `__contains`
  - Can be re-used from pysyft
- JSON path notation: `metadata.channel`, `metadata.author`

**Plan**

1. basic ingestion for existing MCP servers (discord, slack)
2. query builder with basic semantic search for existing MCP servers
3. filtering (pysyft has existing impl for this)
4. data ingestion pipeline for other sources (files?)
5. full text search + hybrid queries with FTS5

### Type System and Generics

**Store class uses generics for type safety:**

```python
# Generic store with default ToolboxDocument
store = ToolboxStore("obsidian")

# Typed store with custom model
store = ToolboxStore("discord", DiscordMessage)

# Subclass for domain-specific functionality
class DiscordStore(ToolboxStore[DiscordMessage]):
    def get_channels(self) -> list[dict]: ...
    def get_users(self) -> list[dict]: ...
```

**Models define their own schema extensions:**

```python
class DiscordMessage(ToolboxDocument):
    channel_id: str
    guild_id: str
    author_id: str

    @classmethod
    def create_schema_extensions(cls, collection: str) -> list[str]:
        return [
            f"ALTER TABLE {collection}_documents ADD COLUMN channel_id TEXT",
            f"CREATE INDEX idx_{collection}_channel ON {collection}_documents(channel_id)",
            # Additional relational tables, indexes, etc.
        ]
```

### Text Chunking

- Uses **semantic-text-splitter** (8MB, Rust-based) for robust text chunking
- Respects sentence boundaries, handles Unicode properly
- Standard API: `TextSplitter(max_characters=1000)`

### Schema Design Decisions

- Models define extra columns directly as pydantic fields (e.g., `DiscordMessage.channel_id`)
- Base tables created automatically, model-specific extensions via `create_schema_extensions()`

### Embedding Strategy

Documents can be embedded either immediately or asynchronously:

```python
# High-volume ingestion - non-blocking (default, requires background worker)
store.insert_documents(slack_messages, embed_immediately=False)

# Critical documents - blocking, immediate semantic search
store.insert_documents([important_doc], embed_immediately=True)
```

**Background worker:**

- Optional background worker to process documents without embeddings
- Continuously processes documents without embeddings
- Allows immediate filter/FTS search while embeddings process
- Can throttle to manage CPU/GPU resources
- Progressive enhancement - semantic search becomes available as embeddings complete
- Simple loop: get documents without embeddings → generate embeddings → update database → sleep

## Migration Notes

No need to write migrations, we can assume a fresh database for MVP.

### slack_mcp

The existing Slack MCP server is largely compatible with the toolbox_store design:

**Compatible aspects:**

- Already uses SQLite with sqlite-vec for embeddings
- Stores documents (messages) with metadata
- Has separate embeddings table with chunks
- Performs semantic search on embeddings

**Required changes:**

- **Table naming**: Migrate from `messages`, `message_embeddings_vec` to `slack_documents`, `slack_embeddings`
- **Schema**: Convert Slack-specific schema to generic format with `id`, `metadata` (JSON), `source`, `content` fields
- **Embeddings**: Replace complex remote Ollama/fastsyftbox setup with local embedder (e.g., sentence-transformers)
- **Chunking**: Current 1:1 message-to-chunk mapping may need proper text chunking for longer content

### discord_mcp

The Discord MCP implementation follows similar patterns to Slack:

**Compatible aspects:**

- Uses SQLite with sqlite-vec (768-dim embeddings)
- Semantic search via `search_messages()` tool
- Background worker for embedding generation
- Similar chunking approach (1:1 message-to-chunk)

**Recommended approach - Hybrid schema:**

- **Keep existing relational tables** (guilds, channels, users, messages) for Discord-specific operations
- **Add `discord_documents` and `discord_embeddings`** tables following toolbox_store pattern
- **Use generated columns** for indexing/querying JSON metadata:
  ```sql
  CREATE TABLE discord_documents (
      id TEXT PRIMARY KEY,
      metadata JSON,
      source TEXT,
      content TEXT,
      -- Real column for FK constraint
      message_id TEXT REFERENCES messages(id),
      -- Generated columns for efficient querying
      channel_id TEXT GENERATED ALWAYS AS (json_extract(metadata, '$.channel_id')) STORED,
      guild_id TEXT GENERATED ALWAYS AS (json_extract(metadata, '$.guild_id')) STORED,
      author_id TEXT GENERATED ALWAYS AS (json_extract(metadata, '$.author_id')) STORED
  );
  CREATE INDEX idx_discord_channel ON discord_documents(channel_id);
  ```
- **Benefits**: Maintains referential integrity, efficient queries, works with generic toolbox_store interface
- **Note**: SQLite doesn't support FKs on generated columns, so critical FKs use real columns

**Required changes:**

- **Embeddings**: Replace Ollama/SyftBox providers with local embedder
- **Store class**: Add Discord-specific search methods that can JOIN with relational tables
