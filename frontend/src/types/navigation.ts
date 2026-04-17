export type AppView = 'dashboard' | 'debate' | 'positions' | 'theses' | 'alerts';

export const VIEW_META: Record<AppView, { title: string; subtitle: string }> = {
  dashboard: {
    title: 'Dashboard',
    subtitle: 'Overview',
  },
  debate: {
    title: 'Debate Lab',
    subtitle: 'Bull vs bear analysis',
  },
  positions: {
    title: 'Positions',
    subtitle: 'Track what you own or watch',
  },
  theses: {
    title: 'My Theses',
    subtitle: 'Beliefs, kill criteria, and change logs',
  },
  alerts: {
    title: 'Alerts',
    subtitle: 'Kill criteria and action queue',
  },
};
