# ComputeDeck plugins

Plugins for [ComputeDeck](https://github.com/JiahaoZhang-Public/computedeck).

| Package                                          | Tools                              | Access                                                                                                                            |
| ------------------------------------------------ | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [Network](network/README.md)                     | Proxy diagnostics and egress tests | Reads network configuration; contacts a fixed HTTPS endpoint and configured IP-addressed SOCKS5 proxies when a test is requested. |
| [Shell credentials](shell-credentials/README.md) | `shell:NAME` credential references | Reads environment variables and literal assignments in credential files. Does not execute shell code.                             |

## Status

The repositories are private and the first package release has not shipped. The official marketplace is empty for now.

Once packages are released, installation will use:

```sh
computedeck plugin marketplace add JiahaoZhang-Public/computedeck-plugins
computedeck plugin install proxy@official
computedeck plugin install shell-credentials@official
```

Install on the machine running the service, then restart ComputeDeck and enable the tools in **Toolbox**. The network package includes both `proxy` and `egress`.

## Contribute

For a fix to an existing plugin, open a PR in this repository. Include the problem, what changes for users and the checks you ran. For a new official plugin, start with a draft PR describing its use and the access it needs.

Plugins specific to your own setup can live in your own repository. Start with `computedeck plugin new my-tool --web`, or use the [Hello example](examples/hello/README.md).

The [contribution guide](CONTRIBUTING.md) covers setup, creating a plugin, local testing and submitting a PR. The [plugin API](https://github.com/JiahaoZhang-Public/computedeck/blob/main/docs/plugins.md) describes the Python and web interfaces.

## Development

Clone `computedeck` and `computedeck-plugins` into adjacent directories. From this checkout:

```sh
uv sync --frozen
npm ci
bash scripts/check.sh
```

CI tests Python 3.12 and 3.13 on macOS and Ubuntu, against the minimum supported core and current `main`. The frontend uses the host's React instance and the plugin API declared in `web/sdk.ts`.

## License and security

[Apache-2.0](LICENSE). See [NOTICE](NOTICE) and [security reporting](SECURITY.md).
