import { z } from 'zod';

// Single source of truth shared between BFF route handlers (validation) and
// React components (typed responses via z.infer). Mirrors FastAPI's Pydantic
// shapes; when those change, update here and `lib/types.ts` re-exports stay
// correct automatically.

export const docStatusSchema = z.enum([
  'pending',
  'processing',
  'ready',
  'failed',
]);

export const documentOutSchema = z.object({
  id: z.string(),
  filename: z.string(),
  status: docStatusSchema,
  page_count: z.number().int().nullable(),
  chunk_count: z.number().int().nullable(),
  error_message: z.string().nullable(),
  uploaded_at: z.string(),
});

export const uploadResponseSchema = z.object({
  doc_id: z.string(),
  status: docStatusSchema,
});

export const searchResultSchema = z.object({
  chunk_id: z.number().int(),
  document_id: z.string(),
  filename: z.string(),
  page: z.number().int().nullable(),
  heading: z.string().nullable(),
  text: z.string(),
  score: z.number(),
});

export const searchResponseSchema = z.object({
  query: z.string(),
  results: z.array(searchResultSchema),
});

export const citationSchema = z.object({
  n: z.number().int(),
  chunk_id: z.number().int(),
  document_id: z.string(),
  filename: z.string(),
  page: z.number().int().nullable(),
  heading: z.string().nullable(),
});

export const chunkRefSchema = z.object({
  chunk_id: z.number().int(),
  document_id: z.string(),
  filename: z.string(),
  page: z.number().int().nullable(),
  heading: z.string().nullable(),
  text: z.string(),
  score: z.number(),
});

export const agentEventSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('text'), delta: z.string() }),
  z.object({
    type: z.literal('tool_use'),
    id: z.string(),
    name: z.string(),
    arguments: z.record(z.string(), z.unknown()),
  }),
  z.object({
    type: z.literal('tool_result'),
    id: z.string(),
    result: z.string(),
    chunks: z.array(chunkRefSchema),
  }),
  z.object({
    type: z.literal('done'),
    answer: z.string(),
    citations: z.array(citationSchema),
  }),
  z.object({
    type: z.literal('error'),
    code: z.string(),
    detail: z.string(),
    retriable: z.boolean(),
  }),
]);

export type DocStatus = z.infer<typeof docStatusSchema>;
export type DocumentOut = z.infer<typeof documentOutSchema>;
export type UploadResponse = z.infer<typeof uploadResponseSchema>;
export type SearchResult = z.infer<typeof searchResultSchema>;
export type SearchResponse = z.infer<typeof searchResponseSchema>;
export type Citation = z.infer<typeof citationSchema>;
export type ChunkRef = z.infer<typeof chunkRefSchema>;
export type AgentEvent = z.infer<typeof agentEventSchema>;
