'use client';

import { Mic, Square } from 'lucide-react';
import * as React from 'react';

import { Button } from '@/components/ui/button';
import { transcribe } from '@/lib/api';

export type MicState = 'idle' | 'rec' | 'busy';

export interface MicButtonProps {
  onText: (text: string) => void;
  // Fires on every internal state transition so the parent can render a
  // contextual indicator (e.g. "Recording…" banner) outside the button.
  onStateChange?: (state: MicState) => void;
}

export function MicButton({ onText, onStateChange }: MicButtonProps) {
  const [state, _setState] = React.useState<MicState>('idle');
  const recorderRef = React.useRef<MediaRecorder | null>(null);
  const chunksRef = React.useRef<Blob[]>([]);

  const setState = React.useCallback(
    (next: MicState) => {
      _setState(next);
      onStateChange?.(next);
    },
    [onStateChange],
  );

  async function start() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setState('busy');
        try {
          const { text } = await transcribe(
            new Blob(chunksRef.current, { type: 'audio/webm' }),
          );
          if (text) onText(text);
        } catch {
          // network / transcription failure — drop back to idle silently
        } finally {
          setState('idle');
        }
      };
      recorder.start();
      recorderRef.current = recorder;
      setState('rec');
    } catch {
      // getUserMedia denied or unavailable
      setState('idle');
    }
  }

  function stop() {
    recorderRef.current?.stop();
  }

  return (
    <Button
      type="button"
      size="icon"
      variant={state === 'rec' ? 'destructive' : 'ghost'}
      disabled={state === 'busy'}
      title={state === 'rec' ? 'Stop recording' : 'Record a question'}
      aria-label={state === 'rec' ? 'Stop recording' : 'Record a question'}
      onClick={() => (state === 'rec' ? stop() : void start())}
    >
      {state === 'rec' ? (
        <Square className="h-4 w-4" />
      ) : (
        <Mic className="h-4 w-4" />
      )}
    </Button>
  );
}
