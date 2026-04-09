import { type Filters } from '../App';

interface Props {
  filters: Filters;
  resultCount: number;
  onClear: () => void;
  showMap: boolean;
  onToggleMap: () => void;
}

const CHIP_STYLES: Record<string, string> = {
  sunny: '☀️ Sunny',
  cloudy: '⛅ Cloudy',
  rainy: '🌧️ Rainy',
  low: '💚 Budget',
  medium: '💚💚 Moderate',
  high: '💚💚💚 Premium',
};

export default function FilterSummary({ filters, resultCount, onClear, showMap, onToggleMap }: Props) {
  const budgetLabel = filters.budget >= 1000000
    ? 'Budget: 1M+ VND'
    : `Budget: ${(filters.budget / 1000).toFixed(0)}k VND`;
  const chips = [
    { label: 'Weather', value: CHIP_STYLES[filters.weather] },
    { label: 'Budget', value: budgetLabel },
    { label: 'Category', value: filters.category === 'all' ? 'All' : filters.category },
    ...(filters.has_kids ? [{ label: 'Kids', value: `${filters.kid_count} child` }] : []),
    { label: 'Time', value: `${filters.time_available}h` },
  ];

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 12, padding: '24px 32px' }}>
      <span style={{ color: 'rgba(255,255,255,0.6)', fontSize: 14 }}>{resultCount} places found</span>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {chips.map(chip => (
          <span
            key={chip.label}
            style={{
              padding: '4px 14px',
              borderRadius: 999,
              background: 'rgba(255,255,255,0.12)',
              backdropFilter: 'blur(4px)',
              color: '#fff',
              fontSize: 12,
              fontWeight: 600,
              border: '1px solid rgba(255,255,255,0.15)',
            }}
          >
            {chip.label}: {chip.value}
          </span>
        ))}
      </div>
      <button
        onClick={onToggleMap}
        style={{
          marginLeft: 'auto',
          padding: '6px 16px',
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 700,
          border: `2px solid ${showMap ? '#fff' : 'rgba(255,255,255,0.35)'}`,
          background: showMap ? '#fff' : 'transparent',
          color: showMap ? '#1A4D2E' : 'rgba(255,255,255,0.75)',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        🗺️ {showMap ? 'Hide Map' : 'Show Map'}
      </button>
      <button
        onClick={onClear}
        style={{
          padding: '6px 16px',
          borderRadius: 999,
          fontSize: 12,
          fontWeight: 600,
          border: '1px solid transparent',
          background: 'transparent',
          color: 'rgba(255,255,255,0.4)',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        ✕ Clear
      </button>
    </div>
  );
}
