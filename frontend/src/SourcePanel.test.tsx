// @vitest-environment jsdom
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { displayedBox, SourcePanel } from './SourcePanel';
import type { Anchor, Document } from './contracts';

describe('source coordinate fidelity', () => {
  it('transforms rotated PDF coordinates without guessing', () => {
    expect(displayedBox([10, 20, 40, 60], 200, 100, 90)).toEqual([140, 10, 180, 40]);
    expect(displayedBox([10, 20, 40, 60], 200, 100, 0)).toEqual([10, 20, 40, 60]);
    expect(displayedBox([10, 20, 40, 60], 200, 100, 270)).toEqual([20, 60, 60, 90]);
  });
  it('reports absent pages instead of inventing evidence', () => {
    render(
      <SourcePanel
        document={{
          paper_id: '00000000-0000-0000-0000-000000000000',
          parser: 'test',
          parser_version: '1',
          warnings: [],
          pages: [],
        }}
        paperId="test"
        pageNumber={1}
        anchor={null}
        onPage={vi.fn()}
        onSpan={vi.fn()}
      />,
    );
    expect(screen.getByText('Original pages appear after parsing.')).toBeTruthy();
    expect(screen.queryByTestId('source-highlight')).toBeNull();
  });
  it('never overlays a new anchor on the previous page while pixels are loading', () => {
    const document: Document = {
      paper_id: 'test',
      parser: 'test',
      parser_version: '1',
      warnings: [],
      pages: [1, 2].map((number) => ({
        id: `p${number}`,
        paper_id: 'test',
        number,
        width: 100,
        height: 100,
        rotation: 0,
        spans: [],
      })),
    };
    const anchor: Anchor = {
      id: 'a1',
      paper_id: 'test',
      span_id: 's1',
      page_number: 1,
      start_char: 0,
      end_char: 4,
      bbox: [1, 1, 10, 10],
      text: 'text',
      source_hash: 'hash',
      localization_precision: 'TEXT_BLOCK',
    };
    const props = {
      document,
      paperId: 'test',
      pageNumber: 1,
      anchor,
      onPage: vi.fn(),
      onSpan: vi.fn(),
    };
    const view = render(<SourcePanel {...props} />);
    const first = screen.getByAltText('Original PDF page 1');
    expect(screen.queryByTestId('source-highlight')).toBeNull();
    fireEvent.load(first);
    expect(screen.getByTestId('source-highlight')).toBeTruthy();
    view.rerender(
      <SourcePanel {...props} pageNumber={2} anchor={{ ...anchor, id: 'a2', page_number: 2 }} />,
    );
    const second = screen.getByAltText('Original PDF page 2');
    expect(second).not.toBe(first);
    expect(screen.queryByTestId('source-highlight')).toBeNull();
    fireEvent.load(first);
    expect(screen.queryByTestId('source-highlight')).toBeNull();
    fireEvent.error(second);
    expect(screen.getByText('Original page could not be loaded.')).toBeTruthy();
    expect(screen.queryByTestId('source-highlight')).toBeNull();
    fireEvent.load(second);
    expect(screen.getByTestId('source-highlight')).toBeTruthy();
    view.unmount();
  });
});
