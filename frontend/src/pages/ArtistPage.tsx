import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { artworkService, type Artwork } from '@/services/artwork';
import { userService, type UserResponse } from '@/services/user';
import { ItemCard } from '@/components/ui/ItemCard';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Loader } from '@/components/ui/Loader';
import { EmptyState } from '@/components/ui/EmptyState';
import { toast } from 'sonner';
import { User, Calendar, Palette } from 'lucide-react';

export const ArtistPage = () => {
  const { artistId } = useParams<{ artistId: string }>();
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [artist, setArtist] = useState<UserResponse['user'] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchArtistData = async () => {
      if (!artistId) return;

      try {
        const [artworksResponse, artistResponse] = await Promise.all([
          artworkService.getArtworksByArtist(artistId),
          userService.getUserById(artistId)
        ]);

        if (artworksResponse.success && artworksResponse.artworks) {
          setArtworks(artworksResponse.artworks);
        }

        if (artistResponse.success && artistResponse.user) {
          setArtist(artistResponse.user);
        }
      } catch (error) {
        toast.error('Failed to load artist data');
        console.error('Error fetching artist data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchArtistData();
  }, [artistId]);

  if (loading) {
    return <Loader text="Loading artist profile..." />;
  }

  if (!artist) {
    return (
      <EmptyState
        icon={User}
        title="Artist Not Found"
        description="The artist you're looking for doesn't exist."
      />
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Artist Profile Header */}
      <div className="text-center mb-8">
        <Avatar className="w-24 h-24 mx-auto mb-4">
          <AvatarImage src={artist.avatarUrl} alt={artist.name} />
          <AvatarFallback className="text-2xl">
            {artist.name.charAt(0).toUpperCase()}
          </AvatarFallback>
        </Avatar>
        <h1 className="text-3xl font-bold mb-2">{artist.name}</h1>
        {artist.bio && (
          <p className="text-muted-foreground max-w-2xl mx-auto mb-4">
            {artist.bio}
          </p>
        )}
        <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <User className="w-4 h-4" />
            <span>{artworks.length} Artworks</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            <span>Joined {new Date(artist.createdAt).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      {/* Artist's Artworks */}
      <div className="mb-6">
        <h2 className="text-2xl font-semibold mb-4">Artworks by {artist.name}</h2>
        {artworks.length === 0 ? (
          <EmptyState
            icon={Palette}
            title="No Artworks"
            description="This artist hasn't published any artworks yet."
          />
        ) : (
          <div className="masonry-grid">
            {artworks.map((artwork) => (
              <div key={artwork._id} className="masonry-item">
                <ItemCard item={artwork} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};