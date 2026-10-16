export const CATEGORY_ICONS = {
  'technology':           'laptop',
  'artificial-intelligence': 'cpu',
  'cybersecurity':        'shield',
  'open-source':          'code-2',
  'business':             'briefcase',
  'finance':              'bar-chart-2',
  'stocks':               'trending-up',
  'cryptocurrency':       'bitcoin',
  'personal-finance':     'wallet',
  'real-estate':          'home',
  'politics':             'landmark',
  'world-news':           'globe',
  'india-news':           'map-pin',
  'science':              'microscope',
  'space':                'rocket',
  'health':               'activity',
  'environment':          'leaf',
  'sports':               'trophy',
  'cricket':              'circle-dot',
  'football':             'circle-dot',
  'basketball':           'disc-3',
  'esports':              'gamepad-2',
  'entertainment':        'sparkles',
  'movies-tv':            'film',
  'travel':               'plane',
  'food':                 'utensils',
  'lifestyle':            'heart',
  'education':            'book-open',
  'automotive':           'car',
  'agriculture':          'sprout',
  'legal':                'scale',
  'history-culture':      'scroll',
};

export function iconHtml(slug, size = 22) {
  const name = CATEGORY_ICONS[slug] || 'newspaper';
  return `<i data-lucide="${name}" style="width:${size}px;height:${size}px;stroke-width:1.8"></i>`;
}
