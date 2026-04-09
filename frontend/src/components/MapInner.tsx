import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { type Attraction } from '../api';

// Fix Leaflet default marker icon in Vite
const leafletFix = (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const CAT_COLORS: Record<string, string> = {
  park: '#2D6A4F',
  museum: '#92520A',
  viewpoint: '#0369A1',
  nature: '#0D9488',
  market: '#C2410C',
  historic: '#BE123C',
  attraction: '#7C3AED',
  other: '#78716C',
};

function coloredIcon(color: string) {
  return L.divIcon({
    html: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="38" viewBox="0 0 28 38">
      <path d="M14 0C6.27 0 0 6.27 0 14C0 24.5 14 38 14 38S28 24.5 28 14C28 6.27 21.73 0 14 0Z" fill="${color}"/>
      <circle cx="14" cy="14" r="6" fill="white"/>
    </svg>`,
    className: '',
    iconSize: [28, 38],
    iconAnchor: [14, 38],
    popupAnchor: [0, -38],
  });
}

interface Props {
  attractions: Attraction[];
}

export default function MapInner({ attractions }: Props) {
  const CENTER: [number, number] = [11.9385, 108.4585];

  return (
    <MapContainer
      center={CENTER}
      zoom={13}
      style={{ height: '100%', width: '100%' }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {attractions.map(a => {
        const coords = a.coordinates;
        if (!coords || coords.length < 2) return null;
        const color = CAT_COLORS[a.category] || CAT_COLORS.other;
        return (
          <Marker
            key={a.osm_id}
            position={[coords[1], coords[0]]}
            icon={coloredIcon(color)}
          >
            <Popup>
              <div className="font-sans min-w-[180px]">
                <strong className="text-sm text-[#1A4D2E]">{a['name:en'] || a.name}</strong>
                {a['name:vi'] && a['name:vi'] !== a['name:en'] && (
                  <p className="text-xs text-stone-500">{a['name:vi']}</p>
                )}
                <p className="text-xs capitalize mt-1 text-stone-500">{a.category}</p>
                {a.reason && (
                  <p className="text-xs italic text-stone-400 mt-1">{a.reason}</p>
                )}
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}
