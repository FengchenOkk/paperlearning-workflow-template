// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { displayedBox, SourcePanel } from './SourcePanel';

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
});
