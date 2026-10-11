import type { SourceNotation } from './contracts';

/** A separate PDF typography view; stored source wording stays unchanged. */
export function notationView(text: string, notes: SourceNotation[] = [], offset = 0): string {
  const chars = Array.from(text);
  let result = [...chars];
  for (const note of [...notes].reverse()) {
    const start = note.start_char - offset;
    const end = note.end_char - offset;
    if (start >= 0 && end <= chars.length && chars.slice(start, end).join('') === note.raw) {
      result = [...result.slice(0, start), ...Array.from(note.display), ...result.slice(end)];
    }
  }
  return result.join('');
}
