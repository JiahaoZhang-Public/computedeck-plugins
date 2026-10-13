# ComputeDeck plugins

Official extensions for [ComputeDeck](https://github.com/JiahaoZhang-Public/computedeck).

| Package                         | Tools                              | Permissions                                                                                                                  |
| ------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `computedeck-network`           | Proxy diagnostics and egress tests | Reads proxy configuration; tests a fixed HTTPS site only on request; authenticates to configured IP-addressed SOCKS5 proxies |
| `computedeck-shell-credentials` | `shell:NAME` credential references | Reads literal assignments from the environment, a private credentials file and the shell profile; never executes shell code  |

The first release is in preparation. The marketplace stays empty until a released wheel
has a real PyPI URL and digest. Do not install a placeholder package or unverified digest.
After release:

```bash
computedeck plugin marketplace add JiahaoZhang-Public/computedeck-plugins
computedeck plugin install proxy@official
computedeck plugin install shell-credentials@official
```

The network wheel provides both `proxy` and `egress`. Enable each tool in the Toolbox.
See [network](network/README.md), [Shell credentials](shell-credentials/README.md),
[contributing](CONTRIBUTING.md) and [security](SECURITY.md).

For development, clone ComputeDeck beside this checkout, then run:

```bash
uv sync
npm ci
bash scripts/check.sh
```

The frontend is built here; it does not import the core source tree. `web/sdk.ts` and its
supporting type declarations are copied from the core's web API, `PLUGIN_API = 1`.
React is supplied by the host. The Vite setup follows `computedeck plugin new --web`.
The minimum source baseline is the initial 0.3.0a0 import until 0.3.0 is released; CI
also tests the latest core `main`. At the stable release, set the minimum baseline to
`v0.3.0` and raise the dependency and plugin `requires` bounds together.

Apache-2.0. See LICENSE and NOTICE.
