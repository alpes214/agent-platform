from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str = 'postgresql+asyncpg://postgres:localdev@localhost:5432/kb'
    # asyncpg SSL mode. 'prefer' negotiates TLS with Neon and falls back to
    # plaintext for local/testcontainers Postgres. Set 'require' in prod.
    db_ssl: str = 'prefer'

    # Embeddings: Voyage AI (OpenAI-shaped /embeddings). voyage-3.5 is 1024-dim,
    # matching the DocChunk.embedding Vector(1024) column.
    embed_base_url: str = 'https://api.voyageai.com/v1'
    embed_model: str = 'voyage-3.5'
    embed_api_key: str = ''
    embed_dim: int = 1024
    embed_batch_size: int = 16
    embed_timeout_seconds: float = 120.0

    # LLM + Whisper: Groq (OpenAI-compatible). llm_api_key/llm_base_url are also
    # used by the /transcribe endpoint to reach Groq's whisper-large-v3.
    # NB: use a model that does proper JSON tool calls — Groq's Llama models
    # (llama-3.3-70b-versatile, llama-4-scout) emit a `<function=...>` text
    # format that fails with 400 tool_use_failed. qwen3-32b / gpt-oss work.
    llm_base_url: str = 'https://api.groq.com/openai/v1'
    llm_model: str = 'qwen/qwen3-32b'
    llm_api_key: str = ''

    docs_chunk_size: int = 800
    docs_chunk_overlap: int = 100
    docs_top_k: int = 5

    search_min_score: float = 0.3
    search_oversample_factor: int = 1
    tool_result_text_max_chars: int = 1500
    llm_timeout_seconds: float = 120.0

    staging_dir: Path = Path('/tmp/ks-staging')

    max_agent_iterations: int = 8
    log_level: str = 'INFO'

    internal_secret: str = ''
    enforce_internal_secret: bool = False

    # Path prefix where SQLAdmin is mounted. Treated as a defence-in-depth
    # secret: even if someone bypasses CF Access by hitting the origin IP
    # directly, they'd still need to know the prefix. Set via ADMIN_PREFIX env.
    admin_prefix: str = 'admin-01a50e77fc25'


settings = Settings()
