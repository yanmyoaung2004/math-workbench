import { describe, expect, it } from "vitest";
import { JsonLinesSession, unwrap, type LineChild } from "./protocol.ts";
import { EngineError } from "./types.ts";

function fakeSpawn(received: string[]) {
  let handler: ((line: string) => void) | null = null;
  const child: LineChild = {
    write: (line: string) => {
      received.push(line);
      return Promise.resolve();
    },
    close: () => Promise.resolve(),
  };
  return {
    spawn: (onLine: (line: string) => void) => {
      handler = onLine;
      return Promise.resolve(child);
    },
    emit: (line: string) => handler?.(line),
  };
}

describe("JsonLinesSession", () => {
  it("frames requests and routes responses FIFO", async () => {
    const received: string[] = [];
    const transport = fakeSpawn(received);
    const session = new JsonLinesSession(transport.spawn);
    await session.start();
    const first = session.request({ op: "parse", input: "2x" });
    const second = session.request({ op: "parse", input: "3x" });
    expect(session.pending).toBe(2);
    transport.emit('{"ok":true,"op":"parse"}\n{"ok":true,"op":"parse"}\n');
    await expect(first).resolves.toMatchObject({ ok: true });
    await expect(second).resolves.toMatchObject({ ok: true });
    expect(received).toHaveLength(2);
    expect(received[0]).toMatch(/"input":"2x"/);
    expect(session.pending).toBe(0);
  });

  it("rejects on malformed JSON", async () => {
    const transport = fakeSpawn([]);
    const session = new JsonLinesSession(transport.spawn);
    await session.start();
    const pending = session.request({ op: "parse" });
    transport.emit("not json\n");
    await expect(pending).rejects.toBeInstanceOf(SyntaxError);
  });

  it("refuses requests before start", async () => {
    const session = new JsonLinesSession(fakeSpawn([]).spawn);
    await expect(session.request({ op: "x" })).rejects.toThrow("not started");
  });
});

describe("unwrap", () => {
  it("throws EngineError with the engine code", () => {
    try {
      unwrap({ ok: false, op: "solve_linear", error: { code: "PARSE_ERROR", message: "bad" } });
      expect.unreachable();
    } catch (err) {
      expect(err).toBeInstanceOf(EngineError);
      expect((err as EngineError).code).toBe("PARSE_ERROR");
    }
  });
});
