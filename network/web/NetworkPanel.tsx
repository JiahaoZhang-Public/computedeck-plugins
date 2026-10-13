import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, Globe2, Laptop, Loader2, RefreshCw, Server, ShieldCheck } from 'lucide-react';
import { hasLocalBridge, requestNetwork } from './network';
import type { NetworkReport, Request } from './network';
import type { Locale } from '../../web/sdk';
import { translate } from './i18n';
import './NetworkPanel.css';

export type Mode = 'status' | 'probe';

export function NetworkDetails({
  report,
  locale = 'en',
}: {
  report: NetworkReport;
  locale?: Locale;
}) {
  const t = (en: string, zh: string) => (locale === 'zh-CN' ? zh : en);
  const value = (text: string | null | undefined) =>
    translate(text ?? t('Unknown', '未知'), locale);
  return (
    <>
      <dl className="network-facts">
        <div>
          <dt>{t('Device', '设备')}</dt>
          <dd>{report.host}</dd>
        </div>
        <div>
          <dt>{t('Interface / gateway', '网络接口 / 网关')}</dt>
          <dd>
            {value(report.route.interface)} / {value(report.route.gateway)}
          </dd>
        </div>
        <div>
          <dt>Mihomo</dt>
          <dd>
            {report.config_active
              ? t('Configuration linked to a running process', '进程已关联配置')
              : t('No linked process', '未发现关联进程')}{' '}
            ·{' '}
            {report.listening
              ? `${t('Listening on port', '监听端口')} ${report.mixed_port}`
              : t('No listening port', '未发现监听端口')}
          </dd>
        </div>
        <div>
          <dt>{t('Routing mode', '分流模式')}</dt>
          <dd>{value(report.mode)}</dd>
        </div>
        <div>
          <dt>{t('System proxies', '系统代理')}</dt>
          <dd>
            {report.system_proxies.some((p) => !p.known)
              ? t('Unavailable', '无法读取')
              : report.system_proxies
                  .filter((p) => p.enabled)
                  .map((p) => `${p.kind}${p.host ? ` ${p.host}:${p.port}` : ''}`)
                  .join(' · ') || t('All disabled', '全部关闭')}
          </dd>
        </div>
      </dl>
      {report.config_path && (
        <p className="network-config">
          {t('Configuration', '配置文件')}: {report.config_path}
        </p>
      )}
      {report.config_error && (
        <p className="network-error" role="alert">
          {value(report.config_error)}
        </p>
      )}
      <div className="network-upstreams">
        <h3>{t('Configured upstreams', '配置中的上游')}</h3>
        {report.upstreams.length === 0 ? (
          <p>{t('No upstreams configured.', '未发现已配置的上游节点。')}</p>
        ) : (
          report.upstreams.map((p, i) => (
            <div className="network-upstream" key={`${p.name}-${i}`}>
              <strong>{p.name}</strong>
              <code>
                {p.type} · {p.host}:{p.port}
              </code>
              {!p.testable && <small>{value(p.note)}</small>}
            </div>
          ))
        )}
      </div>
      <div className="network-prediction">
        <span>{t('Predicted rule for the fixed test site', '固定测试站点的规则预测')}</span>
        <strong>{value(report.predicted_rule)}</strong>
        <p>
          {t(
            'Predicted from the configuration file; the live route inside the proxy is not observed. Applications may bypass Mihomo when system proxies are disabled.',
            '来自磁盘配置，未读取核心的实时选路。系统代理关闭时，普通应用不一定经过 Mihomo。',
          )}
        </p>
      </div>
      <div className="network-results">
        <h3>{t('Observed connections and egress', '实际连接与出口')}</h3>
        <p>
          {t(
            'Only Test egress sends requests. The fixed destination is',
            '仅由“测试出口”触发，固定目标为',
          )}{' '}
          {report.test_url}. {t('Redirects are not followed.', '不跟随重定向。')}
        </p>
        {!report.tested_at && (
          <div className="network-empty">
            {t(
              'No external test yet. Refreshing status does not contact the test site.',
              '尚未进行外网测试。刷新状态不会访问测试站点。',
            )}
          </div>
        )}
        {report.tests.map((test, i) => (
          <article className="network-test" key={`${test.kind}-${i}`}>
            <header>
              <strong>{value(test.name)}</strong>
              <span className={`network-badge ${test.ok ? 'ok' : 'failed'}`}>
                {test.ok ? t('HTTPS verified', 'HTTPS 验证通过') : t('Failed', '未通过')}
              </span>
            </header>
            <div className="network-path" aria-label={`${test.name} ${t('test path', '测试路径')}`}>
              {test.path.map((hop, index) => (
                <span key={index}>
                  {index > 0 && <ArrowRight size={13} />}
                  <code>{value(hop)}</code>
                </span>
              ))}
            </div>
            <dl className="network-result-facts">
              <div>
                <dt>{t('Observed egress IP', '实测出口 IP')}</dt>
                <dd>{test.egress_ip ?? t('Unavailable', '未取得')}</dd>
              </div>
              <div>
                <dt>{t('HTTP / elapsed', 'HTTP / 总耗时')}</dt>
                <dd>
                  {test.http ?? '—'} / {test.seconds == null ? '—' : `${test.seconds.toFixed(2)}s`}
                </dd>
              </div>
              {test.auth !== undefined && (
                <div>
                  <dt>{t('TCP / SOCKS authentication', 'TCP / SOCKS 认证')}</dt>
                  <dd>
                    {test.tcp ? t('Passed', '成功') : t('Failed', '失败')} /{' '}
                    {test.auth ? t('Passed', '成功') : t('Failed', '失败')}
                    {test.auth_ms != null && ` · ${test.auth_ms}ms`}
                  </dd>
                </div>
              )}
              {test.route && (
                <div>
                  <dt>{t('Interface / gateway to proxy', '到代理的接口 / 网关')}</dt>
                  <dd>
                    {value(test.route.interface)} / {value(test.route.gateway)}
                  </dd>
                </div>
              )}
            </dl>
            {test.kind === 'upstream' && (
              <p>
                {t(
                  'This test explicitly uses this SOCKS5 upstream, bypassing Mihomo rules. It does not represent the current browser route.',
                  '本次显式指定这个 SOCKS5 上游，绕过 Mihomo 分流；不代表浏览器当前路径。',
                )}
              </p>
            )}
            {test.kind === 'mixed' && (
              <p>
                {t(
                  'The local port and egress IP are verified; the internal proxy chain is not observed.',
                  '已验证进入本地端口及出口 IP；核心内部的节点链路尚未观测。',
                )}
              </p>
            )}
            {test.error && <p className="network-error">{value(test.error)}</p>}
          </article>
        ))}
        {!report.mixed_testable && (
          <p>
            {t(
              'Local proxy forwarding tests require a linked process, a listening port and a simple configuration that routes the fixed test site directly. Other configurations could resolve extra upstream or subscription domains.',
              '本地核心转发测试未启用：仅检测已关联进程、正在监听且固定站点明确直连的简单配置，避免核心额外解析上游或规则订阅域名。',
            )}
          </p>
        )}
        {report.tested_at && (
          <p>
            {t('Test completed at', '检测完成于')}{' '}
            {new Date(report.tested_at).toLocaleString(locale)}.{' '}
            {t(
              'Results describe that moment. At most four IP-addressed SOCKS5 upstreams are tested.',
              '结果是该时刻的快照，上游最多测试前 4 个 IP SOCKS5 节点。',
            )}
          </p>
        )}
      </div>
    </>
  );
}

function DeviceNetwork({
  title,
  target,
  remote,
  request,
  mode,
  locale,
}: {
  title: string;
  target: 'local' | 'server';
  remote: boolean;
  request: Request;
  mode: Mode;
  locale: Locale;
}) {
  const t = (en: string, zh: string) => (locale === 'zh-CN' ? zh : en);
  const [report, setReport] = useState<NetworkReport | null>(null);
  const [busy, setBusy] = useState<'status' | 'probe' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(
    async (probe: boolean) => {
      setBusy(probe ? 'probe' : 'status');
      setError(null);
      try {
        setReport(await requestNetwork(target, probe, remote, request));
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Diagnostics failed');
      } finally {
        setBusy(null);
      }
    },
    [target, remote, request],
  );
  useEffect(() => {
    if (mode === 'status') void load(false);
  }, [load, mode]);
  return (
    <section className="panel network-device">
      <header className="network-device-header">
        <div>
          {target === 'local' ? <Laptop size={21} /> : <Server size={21} />}
          <h2>{title}</h2>
        </div>
        <div className="network-actions">
          <button
            className="button secondary-button"
            disabled={!!busy}
            onClick={() => void load(mode === 'probe')}
          >
            {busy === 'probe' ? (
              <Loader2 size={14} className="spin" />
            ) : mode === 'probe' ? (
              <Globe2 size={14} />
            ) : (
              <RefreshCw size={14} />
            )}
            {mode === 'probe' ? t('Test egress', '测试出口') : t('Refresh status', '刷新状态')}
          </button>
        </div>
      </header>
      {busy && (
        <p className="network-loading">
          {busy === 'probe'
            ? t(
                'Testing authentication, HTTPS forwarding and egress IP…',
                '正在检测认证、HTTPS 转发和出口 IP…',
              )
            : t('Reading configuration and system status…', '正在读取配置与系统状态…')}
        </p>
      )}
      {error && (
        <p className="network-error" role="alert">
          {translate(error, locale)}
        </p>
      )}
      {error && report && (
        <p>
          {t(
            'Showing the last successful result, not the current attempt.',
            '以下为上次成功读取的结果，并非本次检测结果。',
          )}
        </p>
      )}
      {!report && !busy && !error && mode === 'probe' && (
        <p className="network-loading">
          {t(
            'Select Test egress to request the fixed site and measure the exit IP and timing.',
            '点“测试出口”向固定站点发起请求，查看出口 IP 和耗时。',
          )}
        </p>
      )}
      {report && <NetworkDetails report={report} locale={locale} />}
    </section>
  );
}

export default function NetworkPanel({
  remote,
  request,
  mode = 'status',
  locale = 'en',
}: {
  remote: boolean;
  request: Request;
  mode?: Mode;
  locale?: Locale;
}) {
  const t = (en: string, zh: string) => (locale === 'zh-CN' ? zh : en);
  return (
    <div className="network-panel">
      <div className="network-notice">
        <ShieldCheck size={19} />
        <p>
          {mode === 'status'
            ? t(
                'Reads system and proxy configuration without sending requests or changing system proxies.',
                '只读取系统和代理配置，不发起请求，也不更改系统代理。',
              )
            : t(
                'Tests only the fixed site without following redirects. Upstream domain names are not resolved; usernames and passwords are never sent to this page.',
                '测试只访问固定站点，不跟随重定向。上游域名不会被解析，账号密码不会传到页面。',
              )}
        </p>
      </div>
      {hasLocalBridge() && remote && (
        <DeviceNetwork
          title={t('This device', '本机')}
          target="local"
          remote={remote}
          request={request}
          mode={mode}
          locale={locale}
        />
      )}
      <DeviceNetwork
        title={t('Server', '服务器')}
        target="server"
        remote={remote}
        request={request}
        mode={mode}
        locale={locale}
      />
    </div>
  );
}
