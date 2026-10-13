# Hello

A ComputeDeck plugin. See ComputeDeck's docs/plugins.md for the plugin API.

```bash
uv sync
uv run pytest
uv run computedeck plugin validate .
```

The page lives in web/. Build it into the package before building a wheel:

```bash
npm --prefix web install
npm --prefix web run build
```

Try it in a ComputeDeck checkout or environment:

```bash
uv pip install -e .
computedeck serve   # then switch it on in the Toolbox
```

List it in a marketplace (computedeck-marketplace.json) with a pinned source, for example a
wheel URL and its sha256, so others can run `computedeck plugin install hello@<marketplace>`.
