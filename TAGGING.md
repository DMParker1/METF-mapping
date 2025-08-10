# Tagging Scheme for METF-mapping

This repository documents the METF mapping program — its origins, methods, outputs, and context.  The goal is to provide context into how METF happened, what came before it, what has come after it. 
Version tags mark meaningful narrative or content milestones, not every minor change.

---

## Tag format
v<major>.<minor>-<descriptor>

- **<major>** = major stage in content development (e.g., complete phase of narrative or significant new section).
- **<minor>** = sequential milestone within that stage.
- **<descriptor>** = short, human-readable summary of the content snapshot.

---

## Examples for this repository

- **v0.1-baseline** → First tagged snapshot after initial public setup.  
  Includes: README with context, methods, impetus, publications.md, and initial assets.

- **v0.2-crosslinks** → Added cross-links between README, publications.md, and key figures.

- **v1.0-related-repos** → Added links to related repositories (e.g., targeted MDA, early diagnosis & treatment).

- **v1.1-expanded-context** → Additional background on program precursors and downstream impacts.

- **v2.0-narrative-complete** → Full set of posts, cross-links, and annotated publications in place.

---

## Related repositories (planned)
While METF-mapping focuses on the mapping component, related lines of research may get their own repositories:
- **targeted-MDA** → Documentation and outputs from targeted mass drug administration studies that fed into METF.
- **early-diagnosis-treatment** → Research and programmatic work on diagnosis & treatment networks (precursor and ongoing interest).

---

## Notes
- Only create a tag when a **whole post, section, or related set of edits** is finished.
- Avoid tagging every small edit — commit history already covers that.
- Tags should always be associated with a GitHub Release so they are visible in the Releases tab and citable if needed.
