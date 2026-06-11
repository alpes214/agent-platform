import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Knowledge Search — RAG document Q&A demo',
  description:
    'A small RAG demo: PDF ingestion, vector search, cited answers, voice input. Built on Voyage embeddings, Groq LLM + Whisper, Neon Postgres + pgvector, Next.js BFF, FastAPI + SQLAdmin on Hetzner.',
  robots: { index: true, follow: true },
};

const STACK: Array<[string, string]> = [
  ['Frontend / BFF', 'Next.js 16, React 19, TypeScript, Tailwind v4, shadcn/ui, Zod'],
  ['Backend', 'FastAPI, SQLAlchemy 2.0 async, SQLAdmin'],
  ['Vector store', 'Neon Postgres + pgvector (HNSW, cosine)'],
  ['Embeddings', 'Voyage AI voyage-3.5 (1024-dim)'],
  ['LLM', 'Groq qwen/qwen3-32b (tool-calling), forced retrieval on first turn'],
  ['Speech-to-text', 'Groq whisper-large-v3 via push-to-talk mic'],
  ['Hosting', 'Vercel (frontend + BFF), Hetzner CX22 + Caddy (FastAPI)'],
  ['Edge / auth', 'Cloudflare (WAF, rate limit, Bot Fight Mode), CF Access for admin'],
];

const HIGHLIGHTS: string[] = [
  'Answers are grounded in the indexed corpus — the agent loop forces a search tool call on the first turn before the LLM is allowed to synthesise.',
  'Citations resolve to real document IDs and deep-link to the source PDF page; the bibliography regex is markdown-aware (handles **bold** filenames the LLM occasionally emits).',
  'SSE streaming over a Vercel BFF that pipes the FastAPI agent loop through with AbortSignal cancellation and request-id propagation for distributed tracing.',
  'Operator admin (SQLAdmin) is mounted behind a Cloudflare Access email-OTP policy on a separate orange-clouded host, with an access-log table that captures every visitor by country, city, gate, and path.',
];

export default function LandingPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <section className="space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight">Knowledge Search</h1>
        <p className="text-lg text-muted-foreground">
          A retrieval-augmented document Q&amp;A demo with cited answers, voice
          input, and a small operator admin.
        </p>
      </section>

      <section className="mt-12 space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          What&apos;s interesting
        </h2>
        <ul className="space-y-2 text-sm leading-relaxed">
          {HIGHLIGHTS.map((h) => (
            <li key={h} className="pl-4 relative before:absolute before:left-0 before:content-['·']">
              {h}
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-12 space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Stack
        </h2>
        <dl className="space-y-2 text-sm">
          {STACK.map(([label, value]) => (
            <div key={label} className="grid grid-cols-[10rem_1fr] gap-3">
              <dt className="font-medium text-muted-foreground">{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </section>

    </main>
  );
}
