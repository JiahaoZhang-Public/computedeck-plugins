// Copied from ComputeDeck's web SDK, PLUGIN_API = 1.
import type { ComponentType, ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import type { Health } from './types';
export type Locale = 'en' | 'zh-CN';
export type Request = <T>(path: string, body?: unknown, method?: string) => Promise<T>;
/** What the host passes to every plugin component. */
export interface PluginProps {
  request: Request;
  demo: boolean;
  remote: boolean;
  locale: Locale;
  page: string;
  health: Health | null;
  navigate: (page: string) => void;
}

export type Label = string | Partial<Record<Locale, string>>;

export interface PluginPage {
  id: string;
  label: Label;
  icon: LucideIcon;
  render: (props: PluginProps) => ReactNode;
}

/**
 * Optional UI contributed at build time. Point the COMPUTEDECK_WEB_PLUGINS environment
 * variable at a module whose default export is a WebPlugin[] when building the web app.
 */
export interface WebPlugin {
  id: string;
  /** The server plugin this UI belongs to; while that plugin is off the UI is hidden. */
  requires?: string;
  /** Extra pages, listed under "Tools" in the sidebar. */
  pages?: PluginPage[];
  /** Rendered beside the 24-hour chart on the overview. */
  overview?: ComponentType<PluginProps>;
  /** Rendered on the settings page below the data sources. */
  settings?: ComponentType<PluginProps>;
  /** Rendered above every page; return null when there is nothing to say. */
  banner?: ComponentType<PluginProps>;
}

declare global {
  interface Window {
    ComputeDeck?: { register: (plugin: WebPlugin & { api?: number }) => void };
  }
}
