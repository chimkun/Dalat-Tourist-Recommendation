import { useState, useCallback } from 'react';
import PreferenceForm from './components/PreferenceForm';
import RecommendationGrid from './components/RecommendationGrid';
import FilterSummary from './components/FilterSummary';
import Map from './components/Map';
import { recommend, type Attraction, type RecommendRequest } from './api';

// Mock decoy data
const MOCK_ATTRACTIONS: Attraction[] = [
  {
    osm_id: 'node/decoy_001', name: 'DalAT Test Museum', 'name:vi': 'DalAT Test Museum',
    'name:en': 'DalAT Test Museum', category: 'museum', primary_type: 'museum',
    score: 0.95, reason: 'Perfect for rainy weather — indoor venue • Cultural & educational',
    indoor_outdoor: 'indoor', kid_score: 7, weather_rainy_score: 8, weather_sunny_score: 3,
    price_level: 0, coordinates: [108.450, 11.940], address: '1 Test Street, Da Lat',
    opening_hours: 'Mo-Su 08:00-17:00', estimated_visit_min: 60, distance_km: 0.3,
    phone: '', website: '', has_name: true,
  },
  {
    osm_id: 'node/decoy_002', name: 'Decoy Park for Kids', 'name:vi': 'Decoy Park for Kids',
    'name:en': 'Decoy Park for Kids', category: 'park', primary_type: 'park',
    score: 0.92, reason: 'Great for kids • Best enjoyed in sunny weather • Budget-friendly',
    indoor_outdoor: 'outdoor', kid_score: 10, weather_rainy_score: 2, weather_sunny_score: 8,
    price_level: 0, coordinates: [108.455, 11.945], address: '2 Playground Ave, Da Lat',
    opening_hours: 'Mo-Su 06:00-20:00', estimated_visit_min: 90, distance_km: 0.5,
    phone: '', website: '', has_name: true,
  },
  {
    osm_id: 'node/decoy_003', name: 'Decoy Viewpoint', 'name:vi': 'Decoy Viewpoint',
    'name:en': 'Decoy Viewpoint', category: 'viewpoint', primary_type: 'viewpoint',
    score: 0.88, reason: 'Best enjoyed in sunny weather • Scenic views • Free entry',
    indoor_outdoor: 'outdoor', kid_score: 4, weather_rainy_score: 1, weather_sunny_score: 9,
    price_level: 0, coordinates: [108.460, 11.935], address: 'Hill Top Road, Da Lat',
    opening_hours: '24/7', estimated_visit_min: 30, distance_km: 0.8,
    phone: '', website: '', has_name: true,
  },
  {
    osm_id: 'node/decoy_004', name: 'Decoy Waterfall', 'name:vi': 'Decoy Waterfall',
    'name:en': 'Decoy Waterfall', category: 'nature', primary_type: 'waterfall',
    score: 0.85, reason: 'Beautiful nature • Best in sunny weather • Great for photography',
    indoor_outdoor: 'outdoor', kid_score: 6, weather_rainy_score: 3, weather_sunny_score: 7,
    price_level: 1, coordinates: [108.440, 11.930], address: 'Forest Road, Da Lat',
    opening_hours: 'Mo-Su 07:00-18:00', estimated_visit_min: 60, distance_km: 1.2,
    phone: '', website: '', has_name: true,
  },
  {
    osm_id: 'node/decoy_005', name: 'Decoy Free Market', 'name:vi': 'Decoy Free Market',
    'name:en': 'Decoy Free Market', category: 'market', primary_type: 'marketplace',
    score: 0.80, reason: 'Budget-friendly • Open on weekends • Local shopping & food',
    indoor_outdoor: 'both', kid_score: 5, weather_rainy_score: 6, weather_sunny_score: 3,
    price_level: 1, coordinates: [108.465, 11.950], address: '5 Market Lane, Da Lat',
    opening_hours: 'Mo-Su 06:00-20:00', estimated_visit_min: 45, distance_km: 0.7,
    phone: '', website: '', has_name: true,
  },
];

export interface Filters {
  weather: 'sunny' | 'rainy' | 'cloudy';
  has_kids: boolean;
  kid_count: number;
  budget: number;  // max price in VND
  time_available: number;
  category: string;
  max_distance_km: number | null;
}

const DEFAULT_FILTERS: Filters = {
  weather: 'sunny',
  has_kids: false,
  kid_count: 1,
  budget: 200000,
  time_available: 2,
  category: 'all',
  max_distance_km: null,
};

export default function App() {
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [results, setResults] = useState<Attraction[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [showMap, setShowMap] = useState(false);

  const handleSearch = useCallback(async (f: Filters) => {
    setFilters(f);
    setLoading(true);
    setHasSearched(true);
    try {
      const req: RecommendRequest = {
        weather: f.weather,
        has_kids: f.has_kids,
        kid_count: f.kid_count,
        budget: f.budget,
        time_available: f.time_available,
        category: f.category,
        max_distance_km: f.max_distance_km ?? undefined,
        limit: 20,
      };
      const data = await recommend(req);
      // Prepend mock data so decoys always visible
      const mixed = [...MOCK_ATTRACTIONS, ...data.recommendations];
      setResults(mixed);
    } catch {
      setResults(MOCK_ATTRACTIONS);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleClear = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
    setResults([]);
    setHasSearched(false);
  }, []);

  return (
    <div style={{ minHeight: '100vh', width: '100%' }}>
      {/* ─── Page Header ─── */}
      <header style={{ width: '100%', padding: '64px 32px', textAlign: 'center', color: '#fff' }}>
        <h1 style={{ fontFamily: '"Lato", sans-serif', fontSize: 48, fontWeight: 900, letterSpacing: -1, marginBottom: 12 }}>
          Da Lat Travel Guide
        </h1>
        <p style={{ color: 'rgba(255,255,255,0.65)', fontSize: 16, fontWeight: 300 }}>
          Find the perfect attractions based on weather, your group, and budget
        </p>
      </header>

      {/* ─── Main Content ─── */}
      <PreferenceForm
        filters={filters}
        onSearch={handleSearch}
        onClear={handleClear}
        loading={loading}
      />

      {/* Results Summary */}
      {hasSearched && results.length > 0 && (
        <FilterSummary
          filters={filters}
          resultCount={results.length}
          onClear={handleClear}
          showMap={showMap}
          onToggleMap={() => setShowMap(v => !v)}
        />
      )}

      {/* Map */}
      {showMap && results.length > 0 && (
        <div style={{ padding: '0 32px 48px' }}>
          <Map attractions={results} />
        </div>
      )}

      {/* Cards */}
      {results.length > 0 && (
        <div style={{ padding: '0 32px 80px' }}>
          {results.map((a, i) => (
            <div key={a.osm_id} style={{ animation: `fadeIn 0.3s ease-out ${i * 40}ms forwards`, opacity: 0 }}>
              <RecommendationGrid attractions={[a]} />
            </div>
          ))}
        </div>
      )}

      {/* No results */}
      {!loading && hasSearched && results.length === 0 && (
        <div style={{ textAlign: 'center', padding: '80px 32px', color: 'rgba(255,255,255,0.6)' }}>
          <p style={{ fontSize: 20, fontWeight: 500 }}>No attractions found</p>
          <p style={{ fontSize: 14, marginTop: 8 }}>Try adjusting your filters</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '80px 0' }}>
          <div style={{ height: 40, width: 40, borderRadius: '50%', border: '4px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite' }} />
        </div>
      )}
    </div>
  );
}
