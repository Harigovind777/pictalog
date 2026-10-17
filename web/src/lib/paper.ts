/** The grey seamless papers a catalog can be shot on (defined in index.css). */
export const PAPERS = ['chalk', 'pearl', 'silver', 'ash', 'smoke', 'stone'] as const
export type Paper = (typeof PAPERS)[number]

/** Each catalog keeps one backdrop, on the owner's screens and its shared page alike. */
export function paperFor(catalogId: number): Paper {
  return PAPERS[Math.abs(catalogId) % PAPERS.length]
}
