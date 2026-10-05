# Research workspace

React/TypeScript with Vite is used rather than Next.js: this single-user application needs a client workspace and a FastAPI server, with no SEO/SSR requirement. Strict domain types are generated from Pydantic JSON Schema. Cytoscape supplies real graph rendering, pan, zoom, fit, selection and neighborhood focus.

The workspace has a paper/source navigator, central graph, evidence inspector and original page panel. Search returns node/span matches with anchors; page text can select its associated nodes. The source panel displays a locally rendered original PDF page and overlays real bbox coordinates. It links to the original PDF at the selected page. This avoids CDN/native PDF viewer differences; PDF.js can replace the renderer behind the same anchor contract later.

Colors encode node types; dashed borders/edges identify candidates and solid lines identify supported/verified states. The inspector separately displays epistemic status, verification, confidence, extraction method and uncertainty. Dark/light theme, keyboard focus, graph zoom controls and resizable source/inspector panels support dense reading. Browser persistence stores only selected IDs/view, never a second graph.

Four view controls use server projections. Prerequisite/argument/innovation capabilities are only shown when stored data exists; no generated pretend chains. A page with no extractable text reports that limitation clearly.
