// Re-exports from lib/schemas.ts — single source of truth.
// Existing imports `from '@/lib/types'` keep working unchanged.
export type {
  DocStatus,
  DocumentOut,
  UploadResponse,
  SearchResult,
  SearchResponse,
  Citation,
  ChunkRef,
  AgentEvent,
} from '@/lib/schemas';
