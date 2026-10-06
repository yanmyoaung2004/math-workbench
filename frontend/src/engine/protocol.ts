import { EngineError, type EngineResponse } from "./types.ts";

/** Line-framed JSON transport. Responses arrive FIFO over stdio. */
export interface LineChild {
  write(line: string): Promise<void>;
  close(): Promise<void>;
}

export type SpawnFn = (
  onLine: (line: string) => void,
) => Promise<LineChild>;

interface Pending {
  resolve: (value: EngineResponse) => void;
  reject: (reason: unknown) => void;
}

export class JsonLinesSession {
  private readonly queue: Pending[] = [];
  private child: LineChild | null = null;
  private buffer = "";

  constructor(private readonly spawn: SpawnFn) {}

  async start(): Promise<void> {
    this.child = await this.spawn((chunk) => this.onChunk(chunk));
  }

  async close(): Promise<void> {
    await this.child?.close();
    this.child = null;
  }

  get pending(): number {
    return this.queue.length;
  }

  request(payload: Record<string, unknown>): Promise<EngineResponse> {
    if (!this.child) return Promise.reject(new Error("Session not started."));
    return new Promise<EngineResponse>((resolve, reject) => {
      this.queue.push({ resolve, reject });
      void this.child!
        .write(JSON.stringify(payload) + "\n")
        .catch((err: unknown) => {
          this.queue.splice(
            this.queue.findIndex((p) => p.resolve === resolve),
            1,
          );
          reject(err);
        });
    });
  }

  private onChunk(chunk: string): void {
    this.buffer += chunk;
    let index: number;
    while ((index = this.buffer.indexOf("\n")) >= 0) {
      const line = this.buffer.slice(0, index).trim();
      this.buffer = this.buffer.slice(index + 1);
      if (line) this.route(line);
    }
  }

  private route(line: string): void {
    const next = this.queue.shift();
    if (!next) return; // unsolicited output (e.g. logs) — ignore
    try {
      next.resolve(JSON.parse(line) as EngineResponse);
    } catch (err) {
      next.reject(err);
    }
  }
}

export function unwrap(response: EngineResponse): unknown {
  if (!response.ok) {
    throw new EngineError(response.error.code, response.error.message);
  }
  return response.result;
}
