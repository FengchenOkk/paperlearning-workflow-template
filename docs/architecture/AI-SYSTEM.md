# Scientific AI boundary

The first slice runs without an API key and makes no AI calls. The parser/extractor is deterministic and explicitly labeled. Legacy model profiles are not silently reused; a credential in `.env` is not permission to transmit papers.

Future responsibilities are separate: structure, entities, equations, figures, arguments, prerequisites, external context, verification and translation. Providers must accept/return Pydantic contracts, route by capability, and store provider/model/parameters, input hash, prompt/pipeline version and usage. Scientific evidence gaps must produce UNVERIFIED, not repeated requests until a model invents support.

All future prompts inherit: never invent content, formula IDs, pages, citations, parameters, measurements or conclusions; never relabel inference as paper text or correlation as causality. Cache keys include input hash, model and prompt/pipeline version. Candidate drafts cannot overwrite human verification. No arbitrary natural-language parsing in business logic.
