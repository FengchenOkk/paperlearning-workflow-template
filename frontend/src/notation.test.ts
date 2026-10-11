import { describe, expect, it } from 'vitest';
import type { SourceNotation } from './contracts';
import { notationView } from './notation';

describe('PDF notation view', () => {
  it('keeps source wording separate and locates the barred digit and letter subscript', () => {
    const source = 'α (0235), Qout';
    const notes: SourceNotation[] = [
      {
        start_char: 5,
        end_char: 6,
        raw: '3',
        display: '3̅',
        kind: 'OVERBAR',
        bbox: [1, 1, 2, 2],
        basis: 'PDF_DRAWING_AND_GLYPH',
      },
      {
        start_char: 11,
        end_char: 14,
        raw: 'out',
        display: '_out',
        kind: 'SUBSCRIPT',
        bbox: [1, 1, 2, 2],
        basis: 'PDF_BASELINE_AND_SIZE',
      },
    ];
    expect(notationView(source, notes)).toBe('α (023̅5), Q_out');
    expect(source).toBe('α (0235), Qout');
    expect(notationView('Qout', notes, 10)).toBe('Q_out');
  });

  it('uses Unicode codepoint offsets and refuses a mismatched raw range', () => {
    const note: SourceNotation = {
      start_char: 2,
      end_char: 3,
      raw: '2',
      display: '2̅',
      kind: 'OVERBAR',
      bbox: [1, 1, 2, 2],
      basis: 'PDF_DRAWING_AND_GLYPH',
    };
    expect(notationView('𝛼12', [note])).toBe('𝛼12̅');
    expect(notationView('𝛼13', [note])).toBe('𝛼13');
  });
});
