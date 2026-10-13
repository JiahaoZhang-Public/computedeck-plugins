import type { Locale } from '../../web/sdk';

const phrases: Record<string, string> = {
  'Cannot read proxy configuration; check YAML syntax and file permissions.':
    '无法读取代理配置；请检查 YAML 格式和文件权限。',
  'DIRECT (configuration prediction)': 'DIRECT（配置预测）',
  'GLOBAL (selected upstream not observed)': 'GLOBAL（选择的节点尚未观测）',
  ' (MATCH, configuration prediction)': '（MATCH，配置预测）',
  'Cannot determine statically': '无法静态判断',
  'Dynamic/IP rules require runtime verification': '含动态/IP 规则，需运行时确认',
  'No matching rule configured': '未配置匹配规则',
  'Only plain SOCKS5 upstreams configured by IP are tested; upstream domains are not resolved.':
    '只检测以 IP 配置的普通 SOCKS5，不解析上游域名。',
  'No Mihomo configuration': '无 Mihomo 配置',
  'Upstream closed the connection': '上游关闭连接',
  'SOCKS5 negotiation': 'SOCKS5 协商',
  'Username/password authentication': '账号密码认证',
  'Username or password length does not meet SOCKS5 requirements':
    '账号或密码长度不符合 SOCKS5 要求',
  'Upstream rejected authentication': '上游拒绝认证',
  'Upstream does not accept the offered authentication methods': '上游不接受所提供的认证方式',
  'Proxy resolution failed': '代理解析失败',
  'Test site resolution failed': '测试站点解析失败',
  'Connection failed': '连接失败',
  'Timed out': '超时',
  'TLS handshake failed': 'TLS 握手失败',
  'TLS certificate verification failed': 'TLS 证书验证失败',
  'SOCKS handshake failed': 'SOCKS 握手失败',
  'Test incomplete or invalid egress IP': '测试未完成或返回的出口 IP 无效',
  Diagnostics: '检测程序',
  'Direct connection': '直接连接',
  'Local Mihomo': '本地 Mihomo',
  'Further proxy hops not observed': '核心后续跳转未观测',
  'Fixed site, no redirects; at most four IP-addressed SOCKS5 upstreams are tested.':
    '固定站点、无重定向；上游单独测试最多 4 个 IP SOCKS5 节点。',
  'An egress test is already running; try again shortly.': '出口测速正在进行，请稍后重试。',
  'configuration prediction': '配置预测',
  'This device': '本机',
  'Diagnostics failed': '检测失败',
  'This device requires the desktop bridge; a browser can only inspect the server.':
    '请在更新后的 ComputeDeck 桌面客户端查看本机状态；浏览器只能检测服务器。',
};

export function translate(value: string, locale: Locale): string {
  for (const [en, zh] of Object.entries(phrases)) {
    value = value.replaceAll(locale === 'zh-CN' ? en : zh, locale === 'zh-CN' ? zh : en);
  }
  return value;
}
