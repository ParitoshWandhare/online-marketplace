// @/pages/ArtworkDetailPage.tsx
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Heart, Share, ShoppingCart, ArrowLeft, CreditCard, Plus, Minus, Brush, Star, IndianRupee, ShieldAlert, Calendar, AlertCircle } from 'lucide-react';
import { artworkService } from '@/services/artwork';
import { likeService } from '@/services/like';
import { cartService } from '@/services/cart';
import { visionAiService } from '@/services/visionAi';
import { giftAiService } from '@/services/giftAi';
import { Loader } from '@/components/ui/Loader';
import { toast } from 'sonner';
import { useCopyLink } from '@/hooks/useCopyLink';

declare global {
  interface Window {
    Razorpay: any;
  }
}

export const ArtworkDetailPage = () => {
  const { id } = useParams();
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
  const [complementaryProducts, setComplementaryProducts] = useState<{ product: string; description: string }[]>([]);
  const [loadingComplementary, setLoadingComplementary] = useState(false);
  
  // Vision AI states
  const [visionAnalysis, setVisionAnalysis] = useState<{
    craft?: any;
    quality?: any;
    price?: any;
    fraud?: any;
    occasion?: any;
  }>({});
  const [loadingVision, setLoadingVision] = useState<{
    craft: boolean;
    quality: boolean;
    price: boolean;
    fraud: boolean;
    occasion: boolean;
  }>({
    craft: false,
    quality: false,
    price: false,
    fraud: false,
    occasion: false,
  });

  const { copyLink } = useCopyLink();

  // -------------------- EFFECTS --------------------
  useEffect(() => {
    if (id) fetchArtworkAndLikeStatus();
    loadRazorpayScript();
  }, [id]);

  useEffect(() => {
    if (artwork) {
      fetchAiQualityRating(artwork);
      fetchComplementaryProducts(artwork);
    }
  }, [artwork]);

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

  const handleBuyNow = async () => {
    if (!artwork) return;
    if (quantity > artwork.quantity) {
      toast.error('Not enough stock available');
      return;
    }
    try {
      setBuyingNow(true);
      const orderResponse = await cartService.createDirectOrder([{ artworkId: artwork._id, qty: quantity }]);
      if (!orderResponse.success || !orderResponse.razorpayOrder) {
        toast.error('Failed to create order');
        return;
      }
      const { razorpayOrder } = orderResponse;

      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY_ID || 'your_razorpay_key_id',
        amount: razorpayOrder.amount,
        currency: razorpayOrder.currency,
        name: 'Artisan Marketplace',
        description: `Purchase: ${artwork.title}`,
        order_id: razorpayOrder.id,
        handler: async function (response: any) {
          try {
            const verifyResponse = await cartService.verifyDirectPayment({
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
          name: 'Customer Name',
          email: 'customer@example.com',
          contact: '9999999999',
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
      }
    } catch (error) {
      console.error('AI Quality Prediction error:', error);
    } finally {
      setLoadingQuality(false);
    }
  };

  const fetchComplementaryProducts = async (artwork: any) => {
    if (!artwork.media?.[0]?.url) return;
    try {
      setLoadingComplementary(true);
      const response = await visionAiService.complementaryProducts(await (await fetch(artwork.media[0].url)).blob());
      if (response.success && response.data?.complementary_products) {
        setComplementaryProducts(response.data.complementary_products.slice(0, 3));
      }
    } catch (error) {
      console.error('Complementary products error:', error);
    } finally {
      setLoadingComplementary(false);
    }
  };

  // -------------------- VISION AI ANALYSIS --------------------
  const runVisionAnalysis = async (type: 'craft' | 'quality' | 'price' | 'fraud' | 'occasion') => {
    if (!artwork?.media?.[0]?.url) {
      toast.error('No image available for analysis');
      return;
    }

    // Check if already analyzed
    if (visionAnalysis[type]) {
      return; // Already have data
    }

    try {
      setLoadingVision(prev => ({ ...prev, [type]: true }));
      
      // Fetch image as blob
      const imageBlob = await (await fetch(artwork.media[0].url)).blob();
      const imageFile = new File([imageBlob], 'artwork.jpg', { type: imageBlob.type });

      let result;
      switch (type) {
        case 'craft':
          result = await giftAiService.analyzeCraft(imageFile);
          break;
        case 'quality':
          result = await giftAiService.analyzeQuality(imageFile);
          break;
        case 'price':
          result = await giftAiService.estimatePrice(imageFile);
          break;
        case 'fraud':
          result = await giftAiService.detectFraud(imageFile);
          break;
        case 'occasion':
          result = await giftAiService.detectOccasion(imageFile);
          break;
      }

      if (result.success) {
        setVisionAnalysis(prev => ({ ...prev, [type]: result.data }));
        toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} analysis complete!`);
      } else {
        toast.error(`Failed to analyze ${type}`);
      }
    } catch (error) {
      console.error(`Vision AI ${type} error:`, error);
      toast.error(`Failed to analyze ${type}`);
    } finally {
      setLoadingVision(prev => ({ ...prev, [type]: false }));
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
              <Button size="lg" className="flex-1 btn-gradient" onClick={handleBuyNow} disabled={buyingNow || artwork.quantity === 0}>
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

        {/* People Also Bought */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-6 text-foreground">People Also Bought</h2>
          {loadingComplementary ? (
            <div className="flex justify-center items-center py-6">
              <Loader text="Loading related products..." />
            </div>
          ) : complementaryProducts.length === 0 ? (
            <p className="text-muted-foreground text-center py-6 text-base">No related products found.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {complementaryProducts.map((item, idx) => (
                <Card
                  key={idx}
                  className="group relative overflow-hidden transition-all duration-300 hover:shadow-md hover:-translate-y-1 bg-card border border-border rounded-lg"
                >
                  <CardContent className="p-5">
                    <h3 className="text-lg font-semibold mb-3 text-foreground">{item.product}</h3>
                    <p className="text-sm text-muted-foreground line-clamp-3 mb-4">{item.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Vision AI Analysis Section */}
        <div className="mt-12">
          <h2 className="text-2xl font-bold mb-6 text-foreground">AI-Powered Analysis</h2>
          
          {/* Analysis Buttons */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
            {[
              { type: 'craft' as const, label: 'Craft Type', icon: <Brush className="w-6 h-6" />, color: 'text-blue-600', bg: 'bg-blue-50' },
              { type: 'quality' as const, label: 'Quality', icon: <Star className="w-6 h-6" />, color: 'text-yellow-600', bg: 'bg-yellow-50' },
              { type: 'price' as const, label: 'Price Estimate', icon: <IndianRupee className="w-6 h-6" />, color: 'text-green-600', bg: 'bg-green-50' },
              { type: 'fraud' as const, label: 'Fraud Check', icon: <ShieldAlert className="w-6 h-6" />, color: 'text-red-600', bg: 'bg-red-50' },
              { type: 'occasion' as const, label: 'Occasion', icon: <Calendar className="w-6 h-6" />, color: 'text-purple-600', bg: 'bg-purple-50' },
            ].map((tool) => (
              <Button
                key={tool.type}
                variant="outline"
                onClick={() => runVisionAnalysis(tool.type)}
                disabled={loadingVision[tool.type]}
                className={`h-24 flex flex-col items-center justify-center gap-2 hover:border-purple-400 hover:bg-purple-50 transition-all ${tool.bg} border-2 ${visionAnalysis[tool.type] ? 'border-green-500' : ''}`}
              >
                {loadingVision[tool.type] ? (
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                ) : (
                  <div className={tool.color}>{tool.icon}</div>
                )}
                <span className="text-xs font-semibold">{tool.label}</span>
                {visionAnalysis[tool.type] && <Badge variant="secondary" className="text-[10px] px-1 py-0">✓</Badge>}
              </Button>
            ))}
          </div>

          {/* Analysis Results */}
          <div className="space-y-6">
            {/* Quality Analysis */}
            {visionAnalysis.quality && (
              <Card className="p-6 bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200 shadow-lg">
                <h3 className="text-2xl font-bold text-amber-800 mb-5 flex items-center gap-2">
                  <Star className="w-7 h-7 text-amber-600 fill-amber-600" />
                  Quality Assessment
                </h3>

                {/* Star Rating */}
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex">
                    {[1, 2, 3, 4, 5].map((star) => {
                      const rating = visionAnalysis.quality.quality_rating || 
                                     (visionAnalysis.quality.craftsmanship_score ? Math.round(visionAnalysis.quality.craftsmanship_score * 5) : 0);
                      return (
                        <Star
                          key={star}
                          className={`w-8 h-8 transition-all ${
                            star <= rating
                              ? "text-amber-500 fill-amber-500"
                              : "text-gray-300"
                          }`}
                        />
                      );
                    })}
                  </div>
                  <span className="text-lg font-semibold text-amber-900">
                    {(() => {
                      const score = visionAnalysis.quality.craftsmanship_score;
                      const rating = visionAnalysis.quality.quality_rating || (score ? Math.round(score * 5) : 0);
                      return `${rating}/5`;
                    })()}
                  </span>
                </div>

                {/* Craftsmanship Score */}
                {visionAnalysis.quality.craftsmanship_score !== undefined && (
                  <div className="mb-5">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-amber-800">Craftsmanship</span>
                      <span className="font-semibold text-amber-900">
                        {(visionAnalysis.quality.craftsmanship_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-gradient-to-r from-amber-500 to-yellow-500 h-3 rounded-full transition-all duration-700"
                        style={{ width: `${(visionAnalysis.quality.craftsmanship_score * 100).toFixed(0)}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Quality Label */}
                <div className="mb-4">
                  <Badge
                    className={`text-lg px-4 py-1 ${
                      visionAnalysis.quality.quality === "high"
                        ? "bg-green-100 text-green-800"
                        : visionAnalysis.quality.quality === "medium"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {visionAnalysis.quality.quality?.toUpperCase() || "UNKNOWN"} QUALITY
                  </Badge>
                </div>

                {/* Details */}
                {visionAnalysis.quality.details && (
                  <div className="bg-white/70 p-4 rounded-lg border border-amber-200">
                    <p className="text-sm text-amber-800 leading-relaxed italic">
                      {visionAnalysis.quality.details}
                    </p>
                  </div>
                )}
              </Card>
            )}

            {/* Craft Type */}
            {visionAnalysis.craft && (
              <Card className="p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
                <h4 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                  <Brush className="w-5 h-5" /> Detected Craft Style
                </h4>
                <p className="text-lg font-medium text-blue-900">
                  {visionAnalysis.craft.craft_type || "Unknown Craft"}
                </p>
                {visionAnalysis.craft.confidence && (
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${(visionAnalysis.craft.confidence * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-blue-700">
                      {(visionAnalysis.craft.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
                {visionAnalysis.craft.description && (
                  <p className="text-sm text-blue-700 mt-2 italic">{visionAnalysis.craft.description}</p>
                )}
              </Card>
            )}

            {/* Price Estimate */}
            {visionAnalysis.price && (
              <Card className="p-5 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
                <h4 className="font-semibold text-green-800 mb-3 flex items-center gap-2">
                  <IndianRupee className="w-5 h-5" /> Estimated Market Price
                </h4>
                <p className="text-3xl font-bold text-green-700 text-center">
                  ₹{(visionAnalysis.price.estimated_price || 0).toLocaleString("en-IN")}
                </p>
                {visionAnalysis.price.price_range && (
                  <p className="text-sm text-green-600 text-center mt-1">
                    Range: ₹{visionAnalysis.price.price_range.min} – ₹{visionAnalysis.price.price_range.max}
                  </p>
                )}
              </Card>
            )}

            {/* Fraud Detection */}
            {visionAnalysis.fraud && (
              <Card className={`p-5 border-2 ${visionAnalysis.fraud.is_fraudulent ? "bg-red-50 border-red-300" : "bg-green-50 border-green-300"}`}>
                <h4 className={`font-semibold mb-3 flex items-center gap-2 ${visionAnalysis.fraud.is_fraudulent ? "text-red-800" : "text-green-800"}`}>
                  <ShieldAlert className="w-5 h-5" /> Fraud Risk Assessment
                </h4>
                <p className={`text-2xl font-bold text-center ${visionAnalysis.fraud.is_fraudulent ? "text-red-700" : "text-green-700"}`}>
                  {visionAnalysis.fraud.is_fraudulent ? "High Risk Detected" : "Low Risk - Authentic"}
                </p>
                {visionAnalysis.fraud.red_flags?.length > 0 && (
                  <div className="mt-3 space-y-1">
                    <p className="text-sm font-semibold text-red-800 mb-2">Risk Indicators:</p>
                    {visionAnalysis.fraud.red_flags.map((flag: string, i: number) => (
                      <p key={i} className="text-xs text-red-600 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> {flag}
                      </p>
                    ))}
                  </div>
                )}
              </Card>
            )}

            {/* Occasion Detection */}
            {visionAnalysis.occasion && (
              <Card className="p-5 bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
                <h4 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
                  <Calendar className="w-5 h-5" /> Best Suited For
                </h4>
                <p className="text-xl font-semibold text-purple-900">
                  {visionAnalysis.occasion.occasion || "General Gifting"}
                </p>
                {visionAnalysis.occasion.suggested_events?.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {visionAnalysis.occasion.suggested_events.map((event: string, i: number) => (
                      <Badge key={i} variant="secondary" className="bg-purple-100 text-purple-700">
                        {event}
                      </Badge>
                    ))}
                  </div>
                )}
              </Card>
            )}

            {/* Empty State */}
            {!visionAnalysis.craft && !visionAnalysis.quality && !visionAnalysis.price && !visionAnalysis.fraud && !visionAnalysis.occasion && (
              <div className="text-center py-12 text-muted-foreground">
                <div className="mx-auto w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                  <Brush className="w-10 h-10 text-purple-400" />
                </div>
                <p className="text-lg font-medium">Select an analysis type above</p>
                <p className="text-sm mt-1">Get instant AI-powered insights about this artwork</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};