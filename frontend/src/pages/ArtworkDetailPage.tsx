// @/pages/ArtworkDetailPage.tsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Heart, Share, ShoppingCart, ArrowLeft, CreditCard, Plus, Minus, Brush, Star, IndianRupee, ShieldAlert, Calendar, AlertCircle, MapPin, Plus as PlusIcon } from 'lucide-react';
import { artworkService } from '@/services/artwork';
import { likeService } from '@/services/like';
import { cartService } from '@/services/cart';
import { userService, Address } from '@/services/user';
import { orderService } from '@/services/order';
import { visionAiService } from '@/services/visionAi';
import { giftAiService } from '@/services/giftAi';
import { useAuth } from '@/context/AuthContext';
import { Loader } from '@/components/ui/Loader';
import { toast } from 'sonner';
import { useCopyLink } from '@/hooks/useCopyLink';
import { AddAddressForm } from '@/components/forms/AddAddressForm';

declare global {
  interface Window {
    Razorpay: any;
  }
}

export const ArtworkDetailPage = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [artwork, setArtwork] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isLiked, setIsLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [addingToCart, setAddingToCart] = useState(false);
  const [buyingNow, setBuyingNow] = useState(false);
  const [aiQuality, setAiQuality] = useState<{ rating: string; confidence: number } | null>(null);
  const [loadingQuality, setLoadingQuality] = useState(false);
  
  // Address management
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string>('');
  const [showAddressDialog, setShowAddressDialog] = useState(false);
  const [showAddAddressDialog, setShowAddAddressDialog] = useState(false);

  const { copyLink } = useCopyLink();

  // -------------------- EFFECTS --------------------
  useEffect(() => {
    if (id) fetchArtworkAndLikeStatus();
    loadAddresses();
    loadRazorpayScript();
  }, [id]);

  useEffect(() => {
    if (artwork) {
      fetchAiQualityRating(artwork);
    }
  }, [artwork, user]);

  // -------------------- HELPERS --------------------
  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });
  };

  const loadAddresses = async () => {
    try {
      const response = await userService.getAddresses();
      if (response.success) {
        setAddresses(response.addresses);
        const defaultAddr = response.addresses.find(addr => addr.isDefault);
        if (defaultAddr) {
          setSelectedAddressId(defaultAddr._id);
        }
      }
    } catch (error) {
      console.error('Error loading addresses:', error);
    }
  };

  const getCurrencySymbol = (currency: string) => {
    const symbols: { [key: string]: string } = {
      INR: '₹',
      USD: '$',
      EUR: '€',
      GBP: '£',
    };
    return symbols[currency] || currency;
  };

  const updateQuantity = (newQuantity: number) => {
    if (newQuantity >= 1 && newQuantity <= artwork.quantity) setQuantity(newQuantity);
  };

  const handleShare = () => copyLink(window.location.href, artwork?.title);

  const handleLike = async () => {
    if (!artwork) return;
    try {
      await likeService.toggleLike(artwork._id);
      setIsLiked(!isLiked);
      setLikeCount(prev => (isLiked ? prev - 1 : prev + 1));
      toast.success(isLiked ? 'Removed from wishlist' : 'Added to wishlist');
    } catch {
      toast.error('Failed to update wishlist');
    }
  };

  const handleAddToCart = async () => {
    if (!artwork) return;
    if (quantity > artwork.quantity) {
      toast.error('Not enough stock available');
      return;
    }
    try {
      setAddingToCart(true);
      const response = await cartService.addToCart(artwork._id, quantity);
      if (response.success) toast.success(`Added ${quantity} item(s) to cart`);
    } catch (error: any) {
      console.error('Error adding to cart:', error);
      toast.error(error.response?.data?.message || 'Failed to add to cart');
    } finally {
      setAddingToCart(false);
    }
  };

  const handleAddAddress = async (addressData: any) => {
    try {
      const response = await userService.addAddress(addressData);
      if (response.success) {
        setAddresses([...addresses, response.address]);
        setSelectedAddressId(response.address._id);
        setShowAddAddressDialog(false);
        toast.success('Address added successfully');
      }
    } catch (error) {
      toast.error('Failed to add address');
    }
  };

  const handleBuyNow = async () => {
    if (!artwork) return;
    if (quantity > artwork.quantity) {
      toast.error('Not enough stock available');
      return;
    }

    if (!selectedAddressId) {
      toast.error('Please select a shipping address');
      setShowAddressDialog(true);
      return;
    }

    try {
      setBuyingNow(true);
      
      const orderResponse = await orderService.createDirectOrder({
        artworkId: artwork._id,
        qty: quantity,
        shippingAddressId: selectedAddressId
      });

      if (!orderResponse.success || !orderResponse.razorpayOrder) {
        toast.error('Failed to create order');
        return;
      }

      const { razorpayOrder } = orderResponse;
      const selectedAddress = addresses.find(a => a._id === selectedAddressId);

      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY_ID || 'your_razorpay_key_id',
        amount: razorpayOrder.amount,
        currency: razorpayOrder.currency,
        name: 'Artisan Marketplace',
        description: `Purchase: ${artwork.title}`,
        order_id: razorpayOrder.id,
        handler: async function (response: any) {
          try {
            const verifyResponse = await orderService.verifyPayment({
              razorpayOrderId: response.razorpay_order_id,
              razorpayPaymentId: response.razorpay_payment_id,
              razorpaySignature: response.razorpay_signature,
            });
            if (verifyResponse.success) {
              toast.success('Payment successful!');
              window.location.href = '/orders';
            } else toast.error('Payment verification failed');
          } catch {
            toast.error('Payment verification failed');
          }
        },
        prefill: {
          name: selectedAddress?.fullName || 'Customer',
          contact: selectedAddress?.phone || '9999999999',
        },
        theme: { color: '#3B82F6' },
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
      razorpay.on('payment.failed', function (response: any) {
        toast.error('Payment failed: ' + response.error.description);
      });
    } catch (error: any) {
      console.error('Buy now error:', error);
      toast.error(error.response?.data?.message || 'Failed to process purchase');
    } finally {
      setBuyingNow(false);
    }
  };

  // -------------------- API CALLS --------------------
  const fetchArtworkAndLikeStatus = async () => {
    try {
      const [artworkResponse, likedResponse] = await Promise.all([
        artworkService.getArtworkById(id!),
        likeService.getLikedArtworks(),
      ]);

      if (artworkResponse.success && artworkResponse.artwork) {
        setArtwork(artworkResponse.artwork);
        setLikeCount(artworkResponse.artwork.likeCount || 0);
        setIsLiked(likedResponse.artworks.some(a => a._id === id));
      }
    } catch (error) {
      console.error('Error fetching artwork:', error);
      toast.error('Failed to load artwork details');
    } finally {
      setLoading(false);
    }
  };

  const fetchAiQualityRating = async (artwork: any) => {
    if (!artwork.media?.[0]?.url) return;
    try {
      setLoadingQuality(true);
      const response = await visionAiService.qualityPredictions(await (await fetch(artwork.media[0].url)).blob());
      if (response.success && response.data) {
        const { quality_rating, confidence_score } = response.data;
        setAiQuality({ rating: quality_rating, confidence: confidence_score });
      } else {
        console.log('Quality rating unavailable:', response.error);
      }
    } catch (error) {
      console.error('AI Quality Prediction error:', error);
    } finally {
      setLoadingQuality(false);
    }
  };

  // -------------------- RENDER --------------------
  if (loading) return <Loader text="Loading artwork details..." />;

  if (!artwork)
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Artwork not found</h1>
          <p className="text-muted-foreground mb-4">The artwork you're looking for doesn't exist.</p>
          <Button onClick={() => window.history.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    );

  if (artwork.status !== 'published')
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Artwork not available</h1>
          <p className="text-muted-foreground mb-4">This artwork is currently not available for purchase.</p>
          <Button onClick={() => window.history.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    );

  const selectedAddress = addresses.find(a => a._id === selectedAddressId);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <Button variant="ghost" onClick={() => window.history.back()} className="mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back
        </Button>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Image Gallery */}
          <div className="space-y-4">
            <div className="aspect-square rounded-lg overflow-hidden bg-muted">
              <img src={artwork.media[currentImageIndex]?.url || '/placeholder.svg'} alt={artwork.title} className="w-full h-full object-cover" />
            </div>
            {artwork.media.length > 1 && (
              <div className="flex gap-2 overflow-x-auto">
                {artwork.media.map((media: any, index: number) => (
                  <button
                    key={index}
                    onClick={() => setCurrentImageIndex(index)}
                    className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 ${currentImageIndex === index ? 'border-primary' : 'border-transparent'}`}
                  >
                    <img src={media.url} alt={`${artwork.title} ${index + 1}`} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Details */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">{artwork.title}</h1>
              <p className="text-2xl font-bold text-primary">
                {getCurrencySymbol(artwork.currency)}
                {(artwork.price * quantity).toFixed(2)}
              </p>
            </div>

            {/* Artist Info */}
            <div className="flex items-center gap-4">
              <Avatar className="w-12 h-12">
                <AvatarImage src={artwork.artistId.avatarUrl} />
                <AvatarFallback>{artwork.artistId.name[0]}</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold">{artwork.artistId.name}</h3>
                <p className="text-sm text-muted-foreground">Artist</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Button variant="outline" size="sm" onClick={handleLike} className={isLiked ? 'text-red-500 border-red-500' : ''}>
                <Heart className={`w-4 h-4 mr-2 ${isLiked ? 'fill-current' : ''}`} />
                {isLiked ? 'Liked' : 'Like'} ({likeCount})
              </Button>
              <Button variant="outline" size="sm" onClick={handleShare}>
                <Share className="w-4 h-4 mr-2" /> Share
              </Button>
            </div>

            {/* Shipping Address Section */}
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    Delivery Address
                  </h3>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowAddressDialog(true)}
                  >
                    {selectedAddress ? 'Change' : 'Select'}
                  </Button>
                </div>
                
                {selectedAddress ? (
                  <div className="text-sm space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{selectedAddress.label}</Badge>
                      {selectedAddress.isDefault && (
                        <Badge variant="outline" className="text-xs">Default</Badge>
                      )}
                    </div>
                    <p className="font-medium">{selectedAddress.fullName}</p>
                    <p className="text-muted-foreground">{selectedAddress.addressLine1}</p>
                    {selectedAddress.addressLine2 && (
                      <p className="text-muted-foreground">{selectedAddress.addressLine2}</p>
                    )}
                    <p className="text-muted-foreground">
                      {selectedAddress.city}, {selectedAddress.state} - {selectedAddress.pincode}
                    </p>
                  </div>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    onClick={() => setShowAddAddressDialog(true)}
                  >
                    <PlusIcon className="w-4 h-4 mr-2" />
                    Add Delivery Address
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Artwork Card */}
            <Card>
              <CardContent className="p-6 space-y-2">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Quantity Available:</span>
                  <span className="font-medium">{artwork.quantity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Status:</span>
                  <Badge variant="secondary">{artwork.status}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Currency:</span>
                  <span className="font-medium">{artwork.currency}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">AI Quality Rating:</span>
                  <span className="flex items-center gap-2">
                    {loadingQuality ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                    ) : aiQuality ? (
                      <div className="flex items-center gap-2">
                        <svg className="w-8 h-8" viewBox="0 0 36 36">
                          <path
                            d="M18 2.0845
                               a 15.9155 15.9155 0 0 1 0 31.831
                               a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="#e5e7eb"
                            strokeWidth="3"
                          />
                          <path
                            d="M18 2.0845
                               a 15.9155 15.9155 0 0 1 0 31.831
                               a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke={aiQuality.rating === 'high' ? '#16a34a' : aiQuality.rating === 'medium' ? '#facc15' : '#dc2626'}
                            strokeWidth="3"
                            strokeDasharray={`${aiQuality.confidence * 100}, 100`}
                            strokeLinecap="round"
                          />
                        </svg>
                        <span className="text-sm text-muted-foreground">({(aiQuality.confidence * 100).toFixed(1)}%)</span>
                      </div>
                    ) : (
                      <span className="text-sm text-muted-foreground">N/A</span>
                    )}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Description */}
            {artwork.description && (
              <Card>
                <CardContent className="p-6">
                  <h3 className="font-semibold mb-3">Description</h3>
                  <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">{artwork.description}</p>
                </CardContent>
              </Card>
            )}

            {/* Quantity Selector */}
            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold mb-3">Quantity</h3>
                <div className="flex items-center gap-3">
                  <Button variant="outline" size="sm" onClick={() => updateQuantity(quantity - 1)} disabled={quantity <= 1}>
                    <Minus className="w-4 h-4" />
                  </Button>
                  <Input
                    type="number"
                    value={quantity}
                    onChange={e => {
                      const newQty = parseInt(e.target.value);
                      if (!isNaN(newQty)) updateQuantity(newQty);
                    }}
                    className="w-20 text-center"
                    min="1"
                    max={artwork.quantity}
                  />
                  <Button variant="outline" size="sm" onClick={() => updateQuantity(quantity + 1)} disabled={quantity >= artwork.quantity}>
                    <Plus className="w-4 h-4" />
                  </Button>
                  <span className="text-sm text-muted-foreground">(Max: {artwork.quantity})</span>
                </div>
                <div className="mt-3 text-lg font-semibold">
                  Total: {getCurrencySymbol(artwork.currency)}
                  {(artwork.price * quantity).toFixed(2)}
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4">
              <Button size="lg" variant="outline" className="flex-1" onClick={handleAddToCart} disabled={addingToCart || artwork.quantity === 0}>
                {addingToCart ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
                    Adding...
                  </>
                ) : (
                  <>
                    <ShoppingCart className="w-5 h-5 mr-2" /> Add to Cart
                  </>
                )}
              </Button>
              <Button 
                size="lg" 
                className="flex-1 btn-gradient" 
                onClick={handleBuyNow} 
                disabled={buyingNow || artwork.quantity === 0 || !selectedAddressId}
              >
                {buyingNow ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    <CreditCard className="w-5 h-5 mr-2" /> Buy Now
                  </>
                )}
              </Button>
            </div>

            {artwork.quantity === 0 && (
              <div className="text-center py-4">
                <Badge variant="destructive">Out of Stock</Badge>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Address Selection Dialog */}
      <Dialog open={showAddressDialog} onOpenChange={setShowAddressDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Select Delivery Address</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {addresses.map((address) => (
              <Card
                key={address._id}
                className={`cursor-pointer transition-all ${
                  selectedAddressId === address._id
                    ? 'border-primary ring-2 ring-primary'
                    : 'hover:border-primary/50'
                }`}
                onClick={() => {
                  setSelectedAddressId(address._id);
                  setShowAddressDialog(false);
                }}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{address.label}</Badge>
                      {address.isDefault && (
                        <Badge variant="outline" className="text-xs">Default</Badge>
                      )}
                    </div>
                  </div>
                  <p className="font-medium">{address.fullName}</p>
                  <p className="text-sm text-muted-foreground">{address.addressLine1}</p>
                  {address.addressLine2 && (
                    <p className="text-sm text-muted-foreground">{address.addressLine2}</p>
                  )}
                  <p className="text-sm text-muted-foreground">
                    {address.city}, {address.state} - {address.pincode}
                  </p>
                  <p className="text-sm text-muted-foreground">Phone: {address.phone}</p>
                </CardContent>
              </Card>
            ))}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                setShowAddressDialog(false);
                setShowAddAddressDialog(true);
              }}
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add New Address
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Add Address Dialog */}
      <Dialog open={showAddAddressDialog} onOpenChange={setShowAddAddressDialog}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Address</DialogTitle>
          </DialogHeader>
          <AddAddressForm onSuccess={handleAddAddress} />
        </DialogContent>
      </Dialog>
    </div>
  );
};