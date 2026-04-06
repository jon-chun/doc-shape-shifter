Here's the command to batch convert all PDFs in that subdirectory to Markdown using your `doc-shape-shifter` tool:

```bash
for f in ~/Downloads/asubdir/*.pdf; do uv run --project ~/code/doc-shape-shifter dss "$f" "${f%.pdf}.md"; done
```

Or if you're already `cd`'d into that directory:

```bash
cd ~/Downloads/asubdir
for f in *.pdf; do uv run --project ~/code/doc-shape-shifter dss "$f" "${f%.pdf}.md"; done
```

This loops over every `*.pdf`, strips the `.pdf` extension, and appends `.md` for the output filename — so `report.pdf` becomes `report.md` in the same directory.

If you want verbose output to see which backend is being used for each file:

```bash
for f in ~/Downloads/asubdir/*.pdf; do uv run --project ~/code/doc-shape-shifter dss "$f" "${f%.pdf}.md" -v; done
```

Per the routing rules in your README, `pdf -> md` will prefer `pymupdf4llm` first and fall back to `docling` if needed.