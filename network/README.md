# ComputeDeck network diagnostics

Two tools share this wheel: **Proxy diagnostics** reads local configuration, routes and
system proxy settings; **Egress test** sends requests only when you select Test egress.
Both provide English and Chinese UI. A browser inspects the server. The extra local-device
panel is visible only in remote mode when the desktop bridge is present.

Tests contact only `https://checkip.amazonaws.com/`, never follow redirects, and inspect
at most four plain SOCKS5 upstreams identified by IP. Domain-named upstreams are not resolved.
Tests can authenticate to those proxies using credentials from their configuration. Credentials
are never returned to the page. Forwarding through a local Mihomo port requires a simple,
verified direct rule for the fixed test site. Predicted routes are distinct from observed paths.

Permissions: read proxy configuration and OS networking state; start bounded diagnostic
commands; contact the named HTTPS site and explicitly configured IP SOCKS5 upstreams on request.
Reading status does not contact external sites or change system proxies.

Supports ComputeDeck 0.3 and 0.4 (`PLUGIN_API = 1`). Apache-2.0.

中文：代理诊断只读取服务器的代理配置与网络状态。出口测速只在点击后访问固定 HTTPS
站点，不跟随重定向，不解析上游域名；可向配置中至多四个 IP SOCKS5 上游发送认证。
凭据不会传给页面。远程模式下只有存在桌面桥接时才显示本机检测。预测规则与实测路径分开显示。
