import plugins from '../network/web';

for (const plugin of plugins) {
  window.ComputeDeck?.register({ ...plugin, requires: plugin.id, api: 1 });
}
