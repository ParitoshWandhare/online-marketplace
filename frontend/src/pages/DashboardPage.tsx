import { useState, useEffect } from 'react';
import { StoryBar } from '@/components/ui/StoryBar';
import { ItemCard } from '@/components/ui/ItemCard';
import { Loader } from '@/components/ui/Loader';
import { artworkService, type Artwork } from '@/services/artwork';
import { likeService } from '@/services/like';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';

const DashboardPage = () => {
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [likedArtworks, setLikedArtworks] = useState<Set<string>>(new Set());
  const { user } = useAuth();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [artworksResponse, likedResponse] = await Promise.all([
          artworkService.getAllArtworks(),
          likeService.getLikedArtworks()
        ]);
        
        setArtworks(artworksResponse.artworks);
        setLikedArtworks(new Set(likedResponse.artworks.map(artwork => artwork._id)));
      } catch (error) {
        console.error('Error loading data:', error);
        toast.error('Failed to load artworks');
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchData();
    }
  }, [user]);

  const handleLike = (itemId: string) => {
    setLikedArtworks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  const handleWishlist = (itemId: string) => {
    handleLike(itemId);
  };

  if (loading) {
    return <Loader text="Loading your feed..." />;
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Blinking Festive Offers Banner */}
        <div className="text-center mb-6">
          <Link to="/festive-special">
            <h2 className="text-2xl font-bold text-black-500 animate-bounce">
              🎉 Festive Offers! 🎉
            </h2>
          </Link>
        </div>
        {/* Stories Bar */}
        <h1 className="text-2xl font-bold">New Product Stories</h1>
        <p className="text-muted-foreground">
            Curated just for you from our community of creative sellers
          </p>
        <div className="mb-8 mt-2">
          <StoryBar />
        </div>

        {/* Feed Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">Discover Amazing Products</h1>
          <p className="text-muted-foreground">
            Curated just for you from our community of creative sellers
          </p>
        </div>

        {/* Grid Layout - 4 items per row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {artworks.map((artwork) => (
            <ItemCard
              key={artwork._id}
              item={artwork}
              onLike={handleLike}
              onWishlist={handleWishlist}
              isLiked={likedArtworks.has(artwork._id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;