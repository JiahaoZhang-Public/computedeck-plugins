export interface NetworkTest {
  name: string;
  kind: 'direct' | 'mixed' | 'upstream';
  path: string[];
  ok: boolean;
  tcp?: boolean;
  auth?: boolean;
  auth_ms?: number;
  http?: number;
  seconds?: number;
  peer?: string;
  egress_ip?: string;
  error?: string;
  route?: { interface?: string; gateway?: string };
}
export interface NetworkReport {
  host: string;
  observed_at: string;
  tested_at?: string;
  route: { interface?: string; gateway?: string };
  system_proxies: {
    kind: string;
    enabled: boolean;
    known: boolean;
    host: string | null;
    port: number | null;
  }[];
  config_path: string | null;
  config_error: string | null;
  config_active: boolean;
  mode: string | null;
  mixed_port: number | null;
  listening: boolean;
  upstreams: {
    name: string;
    type: string;
    host: string;
    port: number | null;
    testable: boolean;
    note: string | null;
  }[];
  test_url: string;
  predicted_rule: string;
  mixed_testable: boolean;
  tests: NetworkTest[];
}

export type Request = <T>(path: string, body?: unknown, method?: string) => Promise<T>;
type Bridge = { postMessage(action: 'status' | 'probe'): Promise<NetworkReport> };

function localBridge(): Bridge | undefined {
  if (typeof window === 'undefined') return undefined;
  return (window as Window & { webkit?: { messageHandlers?: { networkDiagnostics?: Bridge } } })
    .webkit?.messageHandlers?.networkDiagnostics;
}

export function hasLocalBridge(): boolean {
  return !!localBridge();
}

export async function requestNetwork(
  target: 'local' | 'server',
  probe: boolean,
  remote: boolean,
  request: Request,
): Promise<NetworkReport> {
  if (target === 'local' && remote) {
    const bridge = localBridge();
    if (!bridge)
      throw new Error(
        'This device requires the desktop bridge; a browser can only inspect the server.',
      );
    return bridge.postMessage(probe ? 'probe' : 'status');
  }
  return probe ? request('/plugins/egress/probe', {}) : request('/plugins/proxy/status');
}
