"""Hello: a ComputeDeck plugin."""

from pathlib import Path
from typing import Any

from computedeck.sdk import Plugin, PluginContext, SettingField


def setup(ctx: PluginContext) -> None:
    """Called once at startup. Routes live under /api/plugins/hello."""

    @ctx.router.get("/hello")
    async def hello() -> dict[str, Any]:
        return {"greeting": ctx.settings()["greeting"]}

    async def on_failure(event: dict[str, Any]) -> None:
        # Events are delivered in order while the plugin is on; see docs/plugins.md.
        job = event["data"].get("job") or {}
        print(f"{job.get('name')} failed on {event['data'].get('source_name')}")

    ctx.on_event(on_failure, ["job.failed"])
    ctx.health = lambda: {"ready": True}


plugin = Plugin(
    id="hello",
    setup=setup,
    name={"en": "Hello", "zh-CN": "Hello"},
    description={"en": "Describe what this tool does.", "zh-CN": "说明这个工具做什么。"},
    # Say plainly what switching it on lets it do; people read this before they do.
    permissions=(
        {"en": "prints failed jobs to the service log", "zh-CN": "把失败的作业写到服务日志"},
    ),
    settings=(
        SettingField(key="greeting", label={"en": "Greeting", "zh-CN": "问候语"}, default="hello"),
    ),
    # Tools that start off are switched on by their owner in the Toolbox.
    default_enabled=False,
    requires=">=0.3,<0.5",
    web=Path(__file__).parent / "web",
)
