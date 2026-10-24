# ComputeDeck Shell credentials

Resolves `shell:NAME` without sourcing or executing a shell profile. It first reads the
process environment. For `Runpod_API_Key` and `GPUHub_API_Key`, it also reads literal
assignments in the ComputeDeck data directory's `credentials.env` and then `~/.zshrc`.
The credentials file must be mode 600. Commands, variable expansion and shell operators
are rejected. Secret values are not displayed in the UI.

Permissions: read environment variables and the named files; no network access.
Supports ComputeDeck 0.3, 0.4, 0.5, 0.6 and 0.7 (`PLUGIN_API = 1`). Apache-2.0.

中文：解析 `shell:变量名`，先读进程环境；对上述两个允许的键，再依次读取数据目录下的
`credentials.env` 和 `~/.zshrc` 中的字面量赋值。凭据文件权限必须为 600。不会执行 shell
配置，不接受命令、变量展开或 shell 运算符；不联网，也不向界面展示凭据。
