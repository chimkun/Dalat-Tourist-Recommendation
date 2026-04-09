import { lazy, Suspense } from 'react';
import { type Attraction } from '../api';

const MapInner = lazy(() => import('./MapInner'));

interface Props {
  attractions: Attraction[];
}

export default function Map({ attractions }: Props) {
  return (
    <div className="rounded-2xl overflow-hidden shadow-lg border border-[#D8F3DC]" style={{ height: '380px' }}>
      <Suspense fallback={
        <div className="h-full flex items-center justify-center bg-[#D8F3DC]">
          <span className="text-[#52B788] font-medium">Loading map...</span>
        </div>
      }>
        <MapInner attractions={attractions} />
      </Suspense>
    </div>
  );
}
