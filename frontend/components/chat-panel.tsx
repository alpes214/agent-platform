'use client';

import { Send } from 'lucide-react';
import * as React from 'react';

import { AskStream } from '@/components/ask-stream';
import { MicButton, type MicState } from '@/components/mic-button';
import { SearchResults } from '@/components/search-results';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { search } from '@/lib/api';
import type { SearchResult } from '@/lib/types';

type Mode = 'ask' | 'search';

export interface ChatPanelProps {
  onOpenViewer: (url: string) => void;
}

export function ChatPanel({ onOpenViewer }: ChatPanelProps) {
  const [mode, setMode] = React.useState<Mode>('ask');
  const [input, setInput] = React.useState('');
  const [submitted, setSubmitted] = React.useState('');
  const [submitNonce, setSubmitNonce] = React.useState(0);
  const [searchResults, setSearchResults] = React.useState<SearchResult[] | null>(null);
  const [searchLoading, setSearchLoading] = React.useState(false);
  const [micState, setMicState] = React.useState<MicState>('idle');
  const inputRef = React.useRef<HTMLTextAreaElement>(null);

  function submitText(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    setInput(trimmed);
    if (mode === 'ask') {
      setSubmitted(trimmed);
      setSubmitNonce((n) => n + 1);
    } else {
      setSearchLoading(true);
      setSubmitted(trimmed);
      void search(trimmed)
        .then((res) => setSearchResults(res.results))
        .catch(() => setSearchResults([]))
        .finally(() => setSearchLoading(false));
    }
  }

  function submit() {
    submitText(input);
  }

  function rephrase() {
    setSubmitted('');
    inputRef.current?.focus();
  }

  return (
    <div className="flex h-full flex-col">
      <Tabs
        value={mode}
        onValueChange={(v) => {
          setMode(v as Mode);
          setSubmitted('');
          setSearchResults(null);
        }}
        className="border-b px-4 py-3"
      >
        <TabsList>
          <TabsTrigger value="ask">Ask</TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="flex-1 min-h-0 overflow-y-auto p-4">
        {mode === 'ask' ? (
          <AskStream
            question={submitted}
            submitNonce={submitNonce}
            onOpenViewer={onOpenViewer}
            onRephrase={rephrase}
            onExampleClick={submitText}
          />
        ) : (
          <SearchResults
            results={searchResults}
            loading={searchLoading}
            query={submitted}
            onOpenViewer={onOpenViewer}
          />
        )}
      </div>

      <form
        className="border-t bg-background p-3"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        {micState === 'rec' && (
          <div className="mb-2 flex items-center gap-2 text-xs text-destructive">
            <span className="inline-block h-2 w-2 rounded-full bg-destructive animate-pulse" />
            Recording — click the stop button to transcribe.
          </div>
        )}
        {micState === 'busy' && (
          <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
            <span className="inline-block h-2 w-2 rounded-full bg-muted-foreground animate-pulse" />
            Transcribing…
          </div>
        )}
        <div className="flex items-end gap-2">
          <Textarea
            ref={inputRef}
            placeholder={mode === 'ask' ? 'Ask anything about your documents...' : 'Search documents...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            className="min-h-[60px] resize-none"
          />
          <MicButton
            onText={(t) => setInput((prev) => (prev ? `${prev} ${t}` : t))}
            onStateChange={setMicState}
          />
          <Button type="submit" size="icon" disabled={!input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
