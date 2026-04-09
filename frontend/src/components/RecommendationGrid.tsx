import { type Attraction } from '../api';

interface Props {
  attractions: Attraction[];
}

export default function RecommendationGrid({ attractions }: Props) {
  return (
    <div className="w-full">
      {attractions.map(attraction => (
        <AttractionCard key={attraction.osm_id} attraction={attraction} />
      ))}
    </div>
  );
}
