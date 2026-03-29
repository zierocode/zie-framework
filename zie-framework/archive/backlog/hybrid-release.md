# hybrid-release

**Problem:** `/zie-release` handles project-specific git ops and publish steps
itself, making the SDLC layer non-generic and fragile across project types.

**Motivation:** Different projects publish differently (gh release, npm publish,
vercel deploy, api-deploy). zie-framework should not know project publish
mechanics — it should only orchestrate the SDLC gates, versioning, and
changelog, then delegate publishing to a project-defined `make release` target.

**Rough scope:**
- Modify `/zie-release` to delegate git ops + publish to `make release NEW=<v>`
- Add readiness gate: scan Makefile for `ZIE-NOT-READY` marker before calling
- Add `zie-init` step to draft and negotiate `make release` skeleton with user
- Update Makefile templates with typed skeletons per project type
