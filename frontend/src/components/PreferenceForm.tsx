import { useState } from 'react';
import { type Filters } from '../App';

interface Props {
  filters: Filters;
  onSearch: (f: Filters) => void;
  onClear: () => void;
  loading: boolean;
}

const WEATHER_OPTIONS = [
  { value: 'sunny', label: 'Sunny', icon: '☀️' },
  { value: 'cloudy', label: 'Cloudy', icon: '⛅' },
  { value: 'rainy', label: 'Rainy', icon: '🌧️' },
] as const;

const CATEGORY_OPTIONS = [
  { value: 'all', label: 'All Attractions' },
  { value: 'park', label: 'Parks & Gardens' },
  { value: 'museum', label: 'Museums' },
  { value: 'viewpoint', label: 'Viewpoints' },
  { value: 'nature', label: 'Nature & Lakes' },
  { value: 'market', label: 'Markets' },
  { value: 'attraction', label: 'Attractions' },
  { value: 'historic', label: 'Historic Sites' },
] as const;

// Budget ticks: 0-100k = 10k steps, 100k-500k = 50k steps, 500k-1M = 100k steps
const BUDGET_TICKS = [
  0, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 90000, 100000,
  150000, 200000, 250000, 300000, 350000, 400000, 450000, 500000,
  600000, 700000, 800000, 900000, 1000000,
];

function formatBudget(v: number): string {
  if (v <= 0) return 'Free';
  if (v >= 1000000) return '1M+ VND';
  return `${(v / 1000).toFixed(0)}k VND`;
}

function budgetToSliderValue(budget: number): number {
  const idx = BUDGET_TICKS.findIndex(t => t >= budget);
  return idx >= 0 ? idx : BUDGET_TICKS.length - 1;
}

function sliderValueToBudget(value: number): number {
  return BUDGET_TICKS[Math.min(value, BUDGET_TICKS.length - 1)];
}

export default function PreferenceForm({ filters, onSearch, onClear, loading }: Props) {
  const [local, setLocal] = useState<Filters>(filters);
  const [sliderVal, setSliderVal] = useState<number>(budgetToSliderValue(filters.budget));

  const submit = () => onSearch(local);

  const set = <K extends keyof Filters>(key: K, value: Filters[K]) => {
    setLocal(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div style={{ width: '100%', minHeight: '100vh', padding: '0 32px' }}>

      {/* ─── Row 1: Weather ─── */}
      <div style={{ paddingTop: 80, paddingBottom: 80 }}>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
          Weather Condition
        </div>
        <div style={{ display: 'flex', gap: 20 }}>
          {WEATHER_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => set('weather', opt.value)}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 12,
                padding: '36px 24px',
                borderRadius: 20,
                border: `2px solid ${local.weather === opt.value ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.25)'}`,
                background: local.weather === opt.value ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.08)',
                color: local.weather === opt.value ? '#fff' : 'rgba(255,255,255,0.75)',
                cursor: 'pointer',
                fontSize: 16,
                fontWeight: 700,
                transition: 'all 0.2s',
              }}
            >
              <span style={{ fontSize: 40 }}>{opt.icon}</span>
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* ─── Row 2: Kids ─── */}
      <div style={{ paddingBottom: 80 }}>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
          Traveling with Children?
        </div>
        <div style={{ display: 'flex', gap: 20 }}>
          <button
            onClick={() => set('has_kids', false)}
            style={{
              flex: 1,
              padding: '28px 24px',
              borderRadius: 20,
              border: `2px solid ${!local.has_kids ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.25)'}`,
              background: !local.has_kids ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.08)',
              color: !local.has_kids ? '#fff' : 'rgba(255,255,255,0.75)',
              cursor: 'pointer',
              fontSize: 16,
              fontWeight: 700,
              transition: 'all 0.2s',
            }}
          >
            Just Adults
          </button>
          <button
            onClick={() => set('has_kids', true)}
            style={{
              flex: 1,
              padding: '28px 24px',
              borderRadius: 20,
              border: `2px solid ${local.has_kids ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.25)'}`,
              background: local.has_kids ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.08)',
              color: local.has_kids ? '#fff' : 'rgba(255,255,255,0.75)',
              cursor: 'pointer',
              fontSize: 16,
              fontWeight: 700,
              transition: 'all 0.2s',
            }}
          >
            👨‍👩‍👧 With Kids
          </button>
        </div>
      </div>

      {/* ─── Row 3: Kid Count ─── */}
      {local.has_kids && (
        <div style={{ paddingBottom: 80 }}>
          <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
            How Many Children?
          </div>
          <div style={{ display: 'flex', gap: 16 }}>
            {[1, 2, 3, 4, 5].map(n => (
              <button
                key={n}
                onClick={() => set('kid_count', n)}
                style={{
                  flex: 1,
                  aspectRatio: '1',
                  maxWidth: 80,
                  borderRadius: 20,
                  border: `2px solid ${local.kid_count === n ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.25)'}`,
                  background: local.kid_count === n ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.08)',
                  color: local.kid_count === n ? '#fff' : 'rgba(255,255,255,0.75)',
                  cursor: 'pointer',
                  fontSize: 22,
                  fontWeight: 700,
                  transition: 'all 0.2s',
                }}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ─── Row 4: Budget (drag slider) ─── */}
      <div style={{ paddingBottom: 80 }}>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
          Budget Level
        </div>
        <div style={{ padding: '28px 24px', borderRadius: 20, background: 'rgba(255,255,255,0.08)', border: '2px solid rgba(255,255,255,0.15)' }}>
          {/* Budget value display */}
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <span style={{ color: '#fff', fontSize: 28, fontWeight: 900 }}>
              {formatBudget(sliderValueToBudget(sliderVal))}
            </span>
            {sliderVal >= BUDGET_TICKS.length - 1 && (
              <span style={{ color: '#fff', fontSize: 16, fontWeight: 700, marginLeft: 8 }}>+</span>
            )}
          </div>
          {/* Slider */}
          <input
            type="range"
            min={0}
            max={BUDGET_TICKS.length - 1}
            step={1}
            value={sliderVal}
            onChange={e => {
              const v = parseInt(e.target.value);
              setSliderVal(v);
              set('budget', sliderValueToBudget(v));
            }}
            style={{ width: '100%', cursor: 'pointer', accentColor: '#fff' }}
          />
          {/* Tick labels */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, color: 'rgba(255,255,255,0.4)', fontSize: 10, fontWeight: 600 }}>
            <span>Free</span>
            <span>100k</span>
            <span>500k</span>
            <span>1M+</span>
          </div>
        </div>
      </div>

      {/* ─── Row 5: Time ─── */}
      <div style={{ paddingBottom: 80 }}>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
          Time Available: <span style={{ color: '#fff', fontWeight: 400, letterSpacing: 0, textTransform: 'none', fontSize: 11 }}>{local.time_available}h</span>
        </div>
        <div style={{ padding: '28px 24px', borderRadius: 20, background: 'rgba(255,255,255,0.08)', border: '2px solid rgba(255,255,255,0.15)' }}>
          <input
            type="range"
            min="0.5"
            max="8"
            step="0.5"
            value={local.time_available}
            onChange={e => set('time_available', parseFloat(e.target.value))}
            style={{ width: '100%', cursor: 'pointer', accentColor: '#fff' }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, color: 'rgba(255,255,255,0.4)', fontSize: 10, fontWeight: 600 }}>
            <span>30min</span>
            <span>2h</span>
            <span>4h</span>
            <span>8h</span>
          </div>
        </div>
      </div>

      {/* ─── Row 6: Category ─── */}
      <div style={{ paddingBottom: 80 }}>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20 }}>
          Category
        </div>
        <select
          value={local.category}
          onChange={e => set('category', e.target.value)}
          style={{
            width: '100%',
            padding: '18px 20px',
            borderRadius: 20,
            background: '#fff',
            color: '#1A4D2E',
            fontSize: 15,
            fontWeight: 600,
            border: '2px solid transparent',
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          {CATEGORY_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* ─── Actions ─── */}
      <div style={{ display: 'flex', gap: 16, paddingBottom: 80 }}>
        <button
          onClick={submit}
          disabled={loading}
          style={{
            flex: 1,
            padding: '22px 24px',
            borderRadius: 20,
            background: '#fff',
            color: '#1A4D2E',
            fontSize: 17,
            fontWeight: 700,
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 10,
            transition: 'all 0.2s',
          }}
        >
          {loading ? '⏳' : '🔍'} Find My Places
        </button>
        <button
          onClick={onClear}
          style={{
            padding: '22px 28px',
            borderRadius: 20,
            background: 'transparent',
            color: 'rgba(255,255,255,0.7)',
            fontSize: 15,
            fontWeight: 700,
            border: '2px solid rgba(255,255,255,0.3)',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          Reset
        </button>
      </div>

    </div>
  );
}
