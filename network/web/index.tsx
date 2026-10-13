// Pages of the two network plugins, bundled together into the computedeck-network package.
// Each page shows only while its own plugin is on.
import { Gauge, Network } from 'lucide-react';
import type { WebPlugin } from '../../web/sdk';
import NetworkPanel from './NetworkPanel';

const plugins: WebPlugin[] = [
  {
    id: 'proxy',
    pages: [
      {
        id: 'proxy',
        label: { 'zh-CN': '代理诊断', en: 'Proxy diagnostics' },
        icon: Network,
        render: ({ request, remote, locale }) => (
          <NetworkPanel remote={remote} request={request} locale={locale} />
        ),
      },
    ],
  },
  {
    id: 'egress',
    pages: [
      {
        id: 'egress',
        label: { 'zh-CN': '出口测速', en: 'Egress test' },
        icon: Gauge,
        render: ({ request, remote, locale }) => (
          <NetworkPanel remote={remote} request={request} locale={locale} mode="probe" />
        ),
      },
    ],
  },
];

export default plugins;
