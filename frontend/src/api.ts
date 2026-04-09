import axios from 'axios';

const API_BASE = '/api';

export interface Attraction {
  osm_id: string;
  name: string;
  'name:vi': string;
  'name:en': string;
  category: string;
  primary_type: string;
  score?: number;
  reason?: string;
  indoor_outdoor: string;
  kid_score: number;
  weather_rainy_score: number;
  weather_sunny_score: number;
  price_level: number;
  coordinates: [number, number];
  address: string;
  opening_hours: string;
  estimated_visit_min: number;
  distance_km: number;
  phone: string;
  website: string;
  has_name: boolean;
  geometry?: object;
}

export interface RecommendRequest {
  weather: 'sunny' | 'rainy' | 'cloudy';
  has_kids: boolean;
  kid_count?: number;
  budget: number;  // max price in VND
  time_available?: number;
  category?: string;
  max_distance_km?: number;
  limit?: number;
}

export interface RecommendResponse {
  recommendations: Attraction[];
  total: number;
  filters_applied: object;
}

const api = axios.create({ baseURL: API_BASE });

export const recommend = async (req: RecommendRequest): Promise<RecommendResponse> => {
  const res = await api.post('/recommend', req);
  return res.data;
};
