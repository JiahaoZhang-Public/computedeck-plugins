# Contributing plugins

Fixes and documentation changes are welcome through PRs. For a new official plugin, start with a draft PR: describe what it does, who would use it, and which files, commands or services it needs to access.

Third-party plugins stay in their authors' repositories and can use their own marketplace. They do not need to be part of the core or copied into this repository.

## Set up the checkouts

You need Python 3.12 or 3.13, uv and Node.js 22. Until public release, you also need access to both private repositories. Clone them beside each other:

```sh
git clone https://github.com/JiahaoZhang-Public/computedeck.git
git clone https://github.com/JiahaoZhang-Public/computedeck-plugins.git
cd computedeck
uv sync --frozen
npm --prefix web ci
npm --prefix web run build
cd ../computedeck-plugins
uv sync --frozen
npm ci
```

The plugin workspace uses the adjacent core checkout. No ComputeDeck package from PyPI is needed.

## Change an existing plugin

Create a branch, make the change and add a test for the behavior it affects. Run:

```sh
bash scripts/check.sh
```

This runs Python and frontend checks, tests and package builds. CI also checks the minimum supported core and latest `main` on macOS and Ubuntu with Python 3.12 and 3.13. The minimum baseline is selected by `CORE_MIN_REF`; it uses the initial 0.3.0a0 import until the stable release. At release, maintainers should move it to `v0.3.0` and update dependency bounds together.

To try the plugins locally, build their pages and start a separate instance:

```sh
npm run build
COMPUTEDECK_WEB_DIR=../computedeck/web/dist \
  uv run computedeck --data-dir .demo-data serve --port 18765 --open
```

Enable the tool you are testing in **Toolbox**, then use **Example data** to try its page. Restart the service after Python changes; rebuild the plugin page after frontend changes.

## Create a plugin

From the `computedeck-plugins` checkout:

```sh
uv run computedeck plugin new lab-tool --web --dir ../computedeck-lab-tool
cd ../computedeck-lab-tool
uv add --editable ../computedeck
uv run pytest
npm --prefix web install
npm --prefix web run build
uv run computedeck plugin validate .
```

The editable dependency uses your local core checkout while packages are unreleased. Keep the package dependency and `Plugin.requires` range consistent with the core versions you support. Use `--driver` when scaffolding a data source, and omit `--web` if you do not need a page.

Add `.demo-data/` to the generated project's `.gitignore`. Start it with the same isolated-service command above, then enable **Lab Tool** in the Toolbox. The generated project is installed in its own environment; installing a plugin in a different environment will not add it to an already-running service.

Use `computedeck.sdk` and the documented web API. `setup(ctx)` should register routes and hooks; perform work only while the plugin is enabled. Describe access in `permissions`, including outbound destinations and commands that change state. Permissions are a description for the user, not a sandbox.

The [plugin API guide](https://github.com/JiahaoZhang-Public/computedeck/blob/main/docs/plugins.md) covers drivers, settings, events, storage and web pages. [examples/hello](examples/hello) is a small working example.

## Submit a PR

Target `main` and keep the change focused. Fill in the [PR template](.github/PULL_REQUEST_TEMPLATE.md) with:

- The problem and the behavior after the change.
- Commands you ran and their results. Include a screenshot for a visible UI change.
- Any change to permissions, dependencies or supported core versions.

Use fictional names, hosts and data in fixtures and screenshots. Never include credentials or production configuration. User-facing labels and permission descriptions should have English and Chinese text. New dependencies must have licenses compatible with Apache-2.0.

A new official plugin also needs package metadata, an entry point, tests, a short README and a built page if it has a UI. Reviewers check that it loads, can be enabled and disabled, and behaves as described. Merge after CI passes and review feedback is addressed.

## Catalog and release PRs

A code PR does not need a catalog entry. The official catalog stays empty until the packages are published; PyPI publishing is currently paused.

After publishing is enabled, the release workflow prepares a separate catalog PR using the released version and the wheel digest from PyPI. Review its source, permissions, dependencies and package contents before merging. Do not add placeholder digests or moving Git references. See [the catalog PR notes](docs/catalog-pr.md).
