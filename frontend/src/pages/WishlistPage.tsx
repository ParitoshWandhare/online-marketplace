import { useState, useEffect } from 'react';
import { ItemCard } from '@/components/ui/ItemCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Heart, Search, Grid, List } from 'lucide-react';
import { likeService } from '@/services/like';
import { Loader } from '@/components/ui/Loader';
import { toast } from 'sonner';
import type { Artwork } from '@/services/artwork';

const WishlistPage = () => {
  const [wishlistItems, setWishlistItems] = useState<Artwork[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLikedArtworks = async () => {
      try {
        const response = await likeService.getLikedArtworks();
        setWishlistItems(response.artworks);
      } catch (error) {
        toast.error('Failed to fetch wishlist items');
      } finally {
        setLoading(false);
      }
    };

    fetchLikedArtworks();
  }, []);

  const handleLike = (itemId: string) => {
    // Remove from wishlist when unliked
    setWishlistItems(prevItems =>
      prevItems.filter(item => item._id !== itemId)
    );
  };

  const handleWishlist = (itemId: string) => {
    setWishlistItems(prevItems =>
      prevItems.filter(item => item._id !== itemId)
    );
  };

  const filteredItems = wishlistItems.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.artistId.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader />
      </div>
    );
  }

  if (wishlistItems.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <EmptyState
            icon={Heart}
            title="Your Wishlist is Empty"
            description="Start browsing and save items you love to see them here"
            action={{
              label: "Browse Products",
              onClick: () => window.location.href = "/dashboard"
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">My Wishlist</h1>
          <p className="text-muted-foreground">
            {wishlistItems.length} {wishlistItems.length === 1 ? 'item' : 'items'} saved for later
          </p>
        </div>

        {/* Search and Controls */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="Search wishlist..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="flex items-center gap-2"
            >
              <Grid className="w-4 h-4" />
              Grid
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="flex items-center gap-2"
            >
              <List className="w-4 h-4" />
              List
            </Button>
          </div>
        </div>

        {/* Wishlist Items */}
        {filteredItems.length > 0 ? (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : 'space-y-4'}>
            {filteredItems.map((item) => (
              <div key={item._id}>
                <ItemCard
                  item={item}
                  onLike={handleLike}
                  onWishlist={handleWishlist}
                  variant={viewMode}
                  isLiked={true}
                />
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Search}
            title="No Items Found"
            description="Try adjusting your search criteria"
          />
        )}
      </div>
    </div>
  );
};

export default WishlistPage;