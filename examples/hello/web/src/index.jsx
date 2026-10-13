import { useEffect, useState } from 'react';

const { components, register } = window.ComputeDeck;
const { Panel } = components;

function Icon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="12" cy="12" r="9" />
    </svg>
  );
}

function Page({ request }) {
  const [greeting, setGreeting] = useState('…');
  useEffect(() => {
    request('/plugins/hello/hello').then((data) => setGreeting(data.greeting));
  }, [request]);
  return (
    <Panel title="Hello">
      <p className="panel-note">{greeting}</p>
    </Panel>
  );
}

register({
  id: 'hello',
  // Hidden while the server plugin of the same id is switched off.
  requires: 'hello',
  pages: [
    {
      id: 'hello',
      label: { en: 'Hello', 'zh-CN': 'Hello' },
      icon: Icon,
      render: (props) => <Page {...props} />,
    },
  ],
});
