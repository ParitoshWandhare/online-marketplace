import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Heart, Share, ShoppingCart } from 'lucide-react';
import { useCopyLink } from '@/hooks/useCopyLink';
import { likeService } from '@/services/like';
import { cartService } from '@/services/cart';
import { useState } from 'react';
import { toast } from 'sonner';
import type { Artwork } from '@/services/artwork';

interface ItemCardProps {
  item: Artwork;
  onLike?: (id: string) => void;
  onWishlist?: (id: string) => void;
  variant?: 'grid' | 'list';
  isLiked?: boolean;
}

export const ItemCard: React.FC<ItemCardProps> = ({ 
  item, 
  onLike, 
  onWishlist, 
  variant = 'grid',
  isLiked = false
}) => {
  const { copyLink } = useCopyLink();
  const [liked, setLiked] = useState(isLiked);
  const [likeCount, setLikeCount] = useState(item.likeCount || 0);
  const [addingToCart, setAddingToCart] = useState(false);

  const handleShare = () => {
    copyLink(`${window.location.origin}/artwork/${item._id}`, item.title);
  };

  const handleLike = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await likeService.toggleLike(item._id);
      setLiked(!liked);
      setLikeCount(prev => liked ? prev - 1 : prev + 1);
      onLike?.(item._id);
    } catch (error) {
      toast.error('Failed to update like');
    }
  };

  const handleWishlist = (e: React.MouseEvent) => {
    e.stopPropagation();
    onWishlist?.(item._id);
  };

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (item.status !== 'published') {
      toast.error('This item is not available for purchase');
      return;
    }

    if (item.quantity === 0) {
      toast.error('This item is out of stock');
      return;
    }

    try {
      setAddingToCart(true);
      const response = await cartService.addToCart(item._id, 1);
      
      if (response.success) {
        toast.success('Added to cart successfully!');
      }
    } catch (error: any) {
      console.error('Error adding to cart:', error);
      toast.error(error.response?.data?.message || 'Failed to add to cart');
    } finally {
      setAddingToCart(false);
    }
  };

  const getCurrencySymbol = (currency: string) => {
    const symbols: { [key: string]: string } = {
      'INR': '₹',
      'USD': '$',
      'EUR': '€',
      'GBP': '£'
    };
    return symbols[currency] || currency;
  };

  return (
    <Card className="card-hover overflow-hidden cursor-pointer" onClick={() => window.location.href = `/artwork/${item._id}`}>
      <div className="relative">
        <img src={item.media?.[0]?.url || '/placeholder.svg'} alt={item.title} className="w-full h-48 object-cover" />
        {item.quantity === 0 && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <span className="text-white font-semibold bg-red-600 px-3 py-1 rounded">Out of Stock</span>
          </div>
        )}
      </div>
      <CardContent className="p-4">
        <h3 className="font-semibold mb-2">{item.title}</h3>
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{item.description}</p>
        <div className="flex justify-between items-center mb-3">
          <span className="text-lg font-bold">{getCurrencySymbol(item.currency)}{item.price}</span>
          <div className="flex items-center gap-2 cursor-pointer" onClick={(e) => { e.stopPropagation(); window.location.href = `/artist/${item.artistId._id}`; }}>
            <Avatar className="w-6 h-6">
              <AvatarImage src={item.artistId.avatarUrl} />
              <AvatarFallback>{item.artistId.name[0]}</AvatarFallback>
            </Avatar>
            <span className="text-sm text-muted-foreground hover:text-primary transition-colors">{item.artistId.name}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLike}
            className={liked ? 'text-red-500' : ''}
          >
            <Heart className={`w-4 h-4 mr-1 ${liked ? 'fill-current' : ''}`} />
            {likeCount}
          </Button>
          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleShare(); }}>
            <Share className="w-4 h-4" />
          </Button>
          <Button 
            size="sm" 
            className="ml-auto btn-gradient" 
            onClick={handleAddToCart}
            disabled={addingToCart || item.quantity === 0 || item.status !== 'published'}
          >
            {addingToCart ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1"></div>
            ) : (
              <ShoppingCart className="w-4 h-4 mr-1" />
            )}
            {item.quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};