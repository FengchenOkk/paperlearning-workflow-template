import { useEffect, useRef } from 'react';
import cytoscape, { type Core } from 'cytoscape';
import type { Graph } from './contracts';

const palette: Record<string, string> = {
  PAPER: '#92a9c2',
  SECTION: '#8092a2',
  METHOD: '#7fc8b1',
  DEFINITION: '#a6c784',
  CLAIM: '#d7ad76',
  RESULT: '#90b9ed',
  EQUATION: '#baa2db',
  FIGURE: '#e29d91',
  TABLE: '#d3c58b',
  FIRST_PRINCIPLE: '#94d4c4',
  THEORY: '#9eb4e9',
};

export function GraphCanvas({
  graph,
  selected,
  onSelect,
  dark,
}: {
  graph: Graph;
  selected: string;
  onSelect: (id: string) => void;
  dark: boolean;
}) {
  const container = useRef<HTMLDivElement>(null);
  const instance = useRef<Core | null>(null);
  const handler = useRef(onSelect);
  useEffect(() => {
    handler.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    if (!container.current) return;
    const cy = cytoscape({
      container: container.current,
      elements: [
        ...graph.nodes.map((n) => ({
          data: {
            id: n.id,
            label: n.label.length > 54 ? `${n.label.slice(0, 54)}…` : n.label,
            color: palette[n.type] ?? '#9dadb8',
            type: n.type,
          },
          classes:
            n.verification_status === 'CANDIDATE' || n.review_current === false ? 'candidate' : '',
        })),
        ...graph.edges.map((e) => ({
          data: {
            id: e.id,
            source: e.source_node_id,
            target: e.target_node_id,
            label: e.relation_type.replaceAll('_', ' ').toLowerCase(),
          },
          classes:
            e.verification_status === 'CANDIDATE' || e.review_current === false ? 'candidate' : '',
        })),
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            label: 'data(label)',
            'font-size': 10,
            color: dark ? '#d6dfeb' : '#243349',
            'text-wrap': 'wrap',
            'text-max-width': '125px',
            'text-valign': 'bottom',
            'text-margin-y': 9,
            width: 24,
            height: 24,
            'border-width': 1,
            'border-color': '#a0b3c5',
          },
        },
        {
          selector: 'node[type = "PAPER"]',
          style: { shape: 'round-rectangle', width: 40, height: 32, 'border-width': 2 },
        },
        { selector: 'node.candidate', style: { 'border-style': 'dashed' } },
        {
          selector: 'edge',
          style: {
            width: 1,
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': '#64768b',
            'line-color': '#64768b',
            label: 'data(label)',
            'font-size': 8,
            color: dark ? '#899aaf' : '#586b82',
            'text-rotation': 'autorotate',
            'text-background-color': dark ? '#141d29' : '#f3f6fa',
            'text-background-opacity': 0.9,
            'text-background-padding': '2px',
          },
        },
        { selector: 'edge.candidate', style: { 'line-style': 'dashed' } },
        { selector: '.faded', style: { opacity: 0.1, 'text-opacity': 0 } },
        { selector: 'node:selected', style: { 'border-color': '#f1be72', 'border-width': 4 } },
      ],
      layout: {
        name: 'cose',
        animate: false,
        nodeRepulsion: () => 15000,
        idealEdgeLength: () => 140,
        padding: 65,
      },
      minZoom: 0.12,
      maxZoom: 4,
    });
    instance.current = cy;
    cy.on('tap', 'node', (e) => handler.current(String(e.target.id())));
    const observer = new ResizeObserver(() => cy.resize());
    observer.observe(container.current);
    return () => {
      observer.disconnect();
      cy.destroy();
      instance.current = null;
    };
  }, [graph, dark]);

  useEffect(() => {
    const cy = instance.current;
    if (!cy) return;
    cy.elements().removeClass('faded');
    cy.nodes().unselect();
    const node = cy.getElementById(selected);
    if (node.length) {
      node.select();
      cy.elements().difference(node.closedNeighborhood()).addClass('faded');
      cy.fit(node.closedNeighborhood(), 100);
      if (cy.zoom() > 1.2) cy.zoom(1.2);
      cy.center(node.closedNeighborhood());
    }
  }, [selected, graph, dark]);

  return (
    <div className="graph-canvas">
      <div
        ref={container}
        className="cytoscape"
        data-testid="graph-canvas"
        aria-label="Interactive scientific knowledge graph"
      />
      <div className="graph-tools">
        <button onClick={() => instance.current?.fit(undefined, 60)} aria-label="Fit graph">
          Fit
        </button>
        <button
          onClick={() => instance.current?.zoom((instance.current?.zoom() ?? 1) * 1.25)}
          aria-label="Zoom in"
        >
          +
        </button>
        <button
          onClick={() => instance.current?.zoom((instance.current?.zoom() ?? 1) / 1.25)}
          aria-label="Zoom out"
        >
          −
        </button>
        <button
          onClick={() => {
            instance.current?.elements().removeClass('faded');
            instance.current?.nodes().unselect();
            instance.current?.fit(undefined, 60);
          }}
          aria-label="Show all nodes"
        >
          Show all
        </button>
      </div>
      <div className="graph-legend">
        <span>
          <i style={{ background: palette.METHOD }} />
          Method
        </span>
        <span>
          <i style={{ background: palette.RESULT }} />
          Result
        </span>
        <span>
          <i style={{ background: palette.EQUATION }} />
          Equation
        </span>
        <span>◌ Candidate</span>
      </div>
      <details className="graph-node-list">
        <summary>Node navigator · {graph.nodes.length}</summary>
        <nav aria-label="Graph node selection">
          {graph.nodes.map((node) => (
            <button key={node.id} data-node-id={node.id} onClick={() => onSelect(node.id)}>
              <small>{node.type}</small>
              {node.label}
            </button>
          ))}
        </nav>
      </details>
    </div>
  );
}
