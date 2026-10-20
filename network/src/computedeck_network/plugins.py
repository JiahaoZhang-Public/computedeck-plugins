"""Two plugins over one diagnostics module: proxy status, and egress tests on demand."""

import asyncio
from pathlib import Path
from typing import Any

from computedeck.sdk import Plugin, PluginContext
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict

from . import diagnostics


class ProbeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


def setup_proxy(ctx: PluginContext) -> None:
    @ctx.router.get("/status")
    async def status() -> dict[str, Any]:
        return await asyncio.to_thread(diagnostics.diagnose)


def setup_egress(ctx: PluginContext) -> None:
    lock = asyncio.Lock()

    @ctx.router.post("/probe")
    async def probe(body: ProbeInput) -> dict[str, Any]:
        if lock.locked():
            raise HTTPException(409, "An egress test is already running; try again shortly.")
        async with lock:
            return await asyncio.to_thread(diagnostics.diagnose, True)


# The run-time UI bundle built by scripts/build-plugin-web.sh; it holds both pages.
WEB = Path(__file__).parent / "web"

proxy = Plugin(
    requires=">=0.3,<0.6",
    icon="network",
    id="proxy",
    setup=setup_proxy,
    name={"en": "Proxy diagnostics", "zh-CN": "代理诊断"},
    description={
        "en": "Routes, system proxies and the Mihomo or Clash configuration of this machine "
        "and the server. Reads only; makes no requests.",
        "zh-CN": "本机与服务器的路由、系统代理和 Mihomo/Clash 配置。只读取，不发起请求。",
    },
    permissions=(
        {
            "en": "reads system proxy settings and the Mihomo configuration",
            "zh-CN": "读取系统代理设置和 Mihomo 配置",
        },
    ),
    page="proxy",
    web=WEB,
)

egress = Plugin(
    requires=">=0.3,<0.6",
    icon="chart",
    id="egress",
    setup=setup_egress,
    name={"en": "Egress test", "zh-CN": "出口测速"},
    description={
        "en": "On request, fetches one fixed site directly, through the local Mihomo port and "
        "through each IP SOCKS5 upstream, and reports the exit IP and timing.",
        "zh-CN": "按需访问一个固定站点：直连、经本机 Mihomo 端口、经每个 IP 形式的 SOCKS5 上游，"
        "给出出口 IP 和耗时。",
    },
    permissions=(
        {
            "en": "requests https://checkip.amazonaws.com/ when you start a test",
            "zh-CN": "开始测试时访问 https://checkip.amazonaws.com/",
        },
        {
            "en": "authenticates to configured SOCKS5 upstreams",
            "zh-CN": "向配置中的 SOCKS5 上游认证",
        },
    ),
    page="egress",
    web=WEB,
)
