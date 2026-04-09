import { useState } from 'react';
import { type Attraction } from '../api';

const CATEGORY_STYLES: Record<string, { bg: string; text: string; icon: string }> = {
  park:       { bg: 'bg-[#D8F3DC]', text: 'text-[#1A4D2E]', icon: '🌳' },
  museum:     { bg: 'bg-[#FFF3E0]', text: 'text-[#92520A]', icon: '🏛️' },
  viewpoint:  { bg: 'bg-[#E0F4FF]', text: 'text-[#0369A1]', icon: '🏔️' },
  nature:     { bg: 'bg-[#F0FDF4]', text: 'text-[#0D9488]', icon: '🌿' },
  market:     { bg: 'bg-[#FEF3E2]', text: 'text-[#C2410C]', icon: '🛒' },
  historic:   { bg: 'bg-[#FFF1F3]', text: 'text-[#BE123C]', icon: '🏛️' },
  attraction: { bg: 'bg-[#F5F0FF]', text: 'text-[#7C3AED]', icon: '🎡' },
  other:      { bg: 'bg-[#F5EEE0]', text: 'text-[#78716C]', icon: '📍' },
};

const PRICE_LABELS = ['Free', 'Budget', 'Moderate', 'Premium'];

function PriceHearts(level: number) {
  const n = Math.round(level);
  return '❤️'.repeat(Math.min(n, 4)) || '🤍';
}

interface Props {
  attraction: Attraction;
}

export default function AttractionCard({ attraction }: Props) {
  const [expanded, setExpanded] = useState(false);
  const cat = attraction.category;
  const style = CATEGORY_STYLES[cat] || CATEGORY_STYLES.other;
  const scorePct = attraction.score != null ? Math.round((attraction.score as number) * 100) : 0;

  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-sm border border-[#D8F3DC]">

      {/* Score bar */}
      <div className="h-1.5 bg-[#D8F3DC]">
        <div
          className="h-full bg-gradient-to-r from-[#2D6A4F] to-[#52B788] transition-all duration-500"
          style={{ width: `${scorePct}%` }}
        />
      </div>

      <div className="p-5">

        {/* Category badge + indoor badge */}
        <div className="flex items-center gap-2 mb-3">
          <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${style.bg} ${style.text}`}>
            {style.icon} {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </span>
          {attraction.indoor_outdoor !== 'both' && (
            <span className="text-xs text-[#52B788] font-medium">
              {attraction.indoor_outdoor === 'indoor' ? '🏠 Indoor' : '☀️ Outdoor'}
            </span>
          )}
          {attraction.indoor_outdoor === 'both' && (
            <span className="text-xs text-[#52B788] font-medium">🏠☀️ Both</span>
          )}
          <span className="ml-auto text-xs font-bold text-[#52B788] bg-[#D8F3DC] px-2 py-0.5 rounded-full">
            {scorePct}%
          </span>
        </div>

        {/* Name */}
        <h3 className="font-serif font-bold text-xl text-[#1A4D2E] mb-1 leading-snug">
          {attraction['name:en'] || attraction.name}
        </h3>
        {attraction['name:vi'] && attraction['name:vi'] !== attraction['name:en'] && (
          <p className="text-sm text-stone-400 mb-2">{attraction['name:vi']}</p>
        )}

        {/* Reason */}
        {attraction.reason && (
          <p className="text-sm text-stone-500 italic leading-relaxed mb-4">
            {attraction.reason}
          </p>
        )}

        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-4 text-sm text-stone-500 mb-4">
          {attraction.kid_score > 0 && (
            <span title="Kid-friendliness" className="flex items-center gap-1">
              👶 {Math.round(attraction.kid_score)}/10
            </span>
          )}
          <span title="Price level" className="flex items-center gap-1">
            {PriceHearts(attraction.price_level)} {PRICE_LABELS[Math.round(attraction.price_level)] || 'Moderate'}
          </span>
          <span title="Visit time" className="flex items-center gap-1">
            ⏱️ {attraction.estimated_visit_min} min
          </span>
          {attraction.distance_km > 0 && (
            <span title="Distance" className="flex items-center gap-1">
              📍 {attraction.distance_km.toFixed(1)} km
            </span>
          )}
        </div>

        {/* Expanded details */}
        {expanded && (
          <div className="border-t border-[#D8F3DC] pt-3 mt-3 space-y-2 text-sm text-stone-600">
            {attraction.address && (
              <p><span className="font-semibold text-[#2D6A4F]">📍</span> {attraction.address}</p>
            )}
            {attraction.opening_hours && (
              <p><span className="font-semibold text-[#2D6A4F]">🕐</span> {attraction.opening_hours}</p>
            )}
            {attraction.phone && (
              <p><span className="font-semibold text-[#2D6A4F]">📞</span> {attraction.phone}</p>
            )}
            {attraction.website && (
              <a
                href={attraction.website}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[#52B788] hover:text-[#2D6A4F] font-medium"
              >
                🌐 Visit website
              </a>
            )}
            {attraction.coordinates && (
              <p className="text-xs text-stone-400">
                {attraction.coordinates[1].toFixed(5)}, {attraction.coordinates[0].toFixed(5)}
              </p>
            )}
          </div>
        )}

        {/* Toggle */}
        <button
          onClick={() => setExpanded(v => !v)}
          className="mt-1 text-sm text-[#52B788] hover:text-[#2D6A4F] font-semibold transition-colors"
        >
          {expanded ? '▲ Less' : '▼ More info'}
        </button>

      </div>
    </div>
  );
}