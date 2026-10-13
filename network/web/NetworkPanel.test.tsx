import { renderToStaticMarkup } from 'react-dom/server';
import { afterEach, describe, expect, it, vi } from 'vitest';
import NetworkPanel, { NetworkDetails } from './NetworkPanel';
import { requestNetwork } from './network';
import type { NetworkReport } from './network';

const report: NetworkReport = {
  host: 'example-client',
  observed_at: '2026-10-01T18:00:00Z',
  route: { interface: 'en0' },
  system_proxies: [{ kind: 'HTTP', enabled: false, known: true, host: null, port: null }],
  config_path: '/example/config.yaml',
  config_error: null,
  config_active: true,
  mode: 'rule',
  mixed_port: 7890,
  listening: true,
  upstreams: [],
  test_url: 'https://checkip.amazonaws.com/',
  predicted_rule: 'DIRECT (MATCH, configuration prediction)',
  mixed_testable: true,
  tests: [],
};
afterEach(() => vi.unstubAllGlobals());

describe('network diagnostics device boundaries', () => {
  it('uses the desktop bridge to inspect this device', async () => {
    const postMessage = vi.fn().mockResolvedValue(report);
    vi.stubGlobal('window', {
      webkit: { messageHandlers: { networkDiagnostics: { postMessage } } },
    });
    const request = vi.fn();
    await requestNetwork('local', true, true, request);
    expect(postMessage).toHaveBeenCalledWith('probe');
    expect(request).not.toHaveBeenCalled();
    const html = renderToStaticMarkup(<NetworkPanel remote request={request} />);
    expect(html).toContain('This device');
    expect(html).toContain('Server');
  });
  it('hides this-device diagnostics without the desktop bridge', async () => {
    vi.stubGlobal('window', {});
    const request = vi.fn();
    await expect(requestNetwork('local', false, true, request)).rejects.toThrow('desktop bridge');
    for (const remote of [true, false]) {
      const html = renderToStaticMarkup(<NetworkPanel remote={remote} request={request} />);
      expect(html).not.toContain('This device');
      expect(html).toContain('Server');
    }
    expect(request).not.toHaveBeenCalled();
  });
  it('reads status from proxy and tests through egress', async () => {
    const request = vi.fn().mockResolvedValue(report);
    await requestNetwork('server', false, true, request);
    expect(request).toHaveBeenLastCalledWith('/plugins/proxy/status');
    await requestNetwork('server', true, true, request);
    expect(request).toHaveBeenLastCalledWith('/plugins/egress/probe', {});
  });
  it.each(['en', 'zh-CN'] as const)('renders %s without starting an external test', (locale) => {
    const request = vi.fn();
    const status = renderToStaticMarkup(<NetworkPanel remote request={request} locale={locale} />);
    const probe = renderToStaticMarkup(
      <NetworkPanel remote request={request} locale={locale} mode="probe" />,
    );
    const refresh = locale === 'en' ? 'Refresh status' : '刷新状态';
    const test = locale === 'en' ? 'Test egress' : '测试出口';
    expect(status).toContain(refresh);
    expect(status).not.toContain(test);
    expect(probe).toContain(test);
    expect(probe).not.toContain(refresh);
    expect(request).not.toHaveBeenCalled();
  });
  it.each(['en', 'zh-CN'] as const)(
    'keeps predictions distinct from observed paths in %s',
    (locale) => {
      const html = renderToStaticMarkup(
        <NetworkDetails
          locale={locale}
          report={{
            ...report,
            tested_at: report.observed_at,
            tests: [
              {
                name: 'Local Mihomo',
                kind: 'mixed',
                path: ['Diagnostics', '127.0.0.1:7890', 'Further proxy hops not observed'],
                ok: true,
                http: 200,
                seconds: 1.2,
                egress_ip: '192.0.2.9',
              },
            ],
          }}
        />,
      );
      expect(html).toContain('192.0.2.9');
      expect(html).toContain(locale === 'en' ? 'configuration prediction' : '配置预测');
      expect(html).toContain(
        locale === 'en' ? 'internal proxy chain is not observed' : '核心内部的节点链路尚未观测',
      );
    },
  );
});
