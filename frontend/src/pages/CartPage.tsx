import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Minus, Plus, Trash2, ShoppingCart, ArrowLeft, CreditCard } from 'lucide-react';
import { cartService, type Cart } from '@/services/cart';
import { artworkService } from '@/services/artwork';
import { Loader } from '@/components/ui/Loader';
import { EmptyState } from '@/components/ui/EmptyState';
import { useToast } from '@/hooks/use-toast';
import { toast } from 'sonner';

declare global {
  interface Window {
    Razorpay: any;
  }
}

interface PopulatedCartItem {
  artworkId: string;
  artwork: {
    _id: string;
    title: string;
    price: number;
    currency: string;
    media: Array<{ url: string; type: string }>;
    quantity: number;
    status: string;
  } | null;
  qty: number;
}

const CartPage = () => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [populatedItems, setPopulatedItems] = useState<PopulatedCartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [total, setTotal] = useState(0);
  const { toast: hookToast } = useToast();

  useEffect(() => {
    loadCart();
    loadRazorpayScript();
  }, []);

  const loadRazorpayScript = () => {
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.onload = () => {
        resolve(true);
      };
      script.onerror = () => {
        resolve(false);
      };
      document.body.appendChild(script);
    });
  };

  const loadCart = async () => {
    try {
      const response = await cartService.getCart();
      if (response.success && response.cart) {
        setCart(response.cart);
        setTotal(response.total || 0);
        
        // If cart has items but they're not populated, fetch artwork details
        if (response.cart.items && response.cart.items.length > 0) {
          await populateCartItems(response.cart.items);
        } else {
          setPopulatedItems([]);
        }
      } else {
        // Handle case where cart doesn't exist yet
        setCart({ _id: '', userId: '', items: [], createdAt: '', updatedAt: '' });
        setPopulatedItems([]);
        setTotal(0);
      }
    } catch (error) {
      console.error('Error loading cart:', error);
      // Set empty cart on error
      setCart({ _id: '', userId: '', items: [], createdAt: '', updatedAt: '' });
      setPopulatedItems([]);
      setTotal(0);
      toast.error('Failed to load cart');
    } finally {
      setLoading(false);
    }
  };

  const populateCartItems = async (items: any[]) => {
  const populated: PopulatedCartItem[] = [];

  for (const item of items) {
    try {
      // --- Normalize artworkId ---
      let artworkId: string = '';
      if (typeof item.artworkId === 'string') {
        artworkId = item.artworkId;
      } else if (item.artworkId?._id) {
        artworkId = item.artworkId._id;
      } else if (item.artworkId?.$oid) {
        artworkId = item.artworkId.$oid;
      }

      // --- Normalize qty ---
      let qty: number = item.qty;
      if (item.qty?.$numberInt) {
        qty = parseInt(item.qty.$numberInt, 10);
      }

      // --- If already populated with artwork details ---
      if (typeof item.artworkId === 'object' && item.artworkId._id) {
        populated.push({
          artworkId,
          artwork: item.artworkId,
          qty,
        });
      } else {
        // --- Fetch artwork details from service ---
        const artworkResponse = await artworkService.getArtworkById(artworkId);
        populated.push({
          artworkId,
          artwork: artworkResponse.success ? artworkResponse.artwork : null,
          qty,
        });
      }
    } catch (error) {
      console.error('Error fetching artwork details:', error);

      let artworkId = typeof item.artworkId === 'string'
        ? item.artworkId
        : item.artworkId?._id || item.artworkId?.$oid;

      let qty = item.qty?.$numberInt
        ? parseInt(item.qty.$numberInt, 10)
        : item.qty;

      populated.push({
        artworkId,
        artwork: null,
        qty,
      });
    }
  }

  setPopulatedItems(populated);

  // --- Calculate total ---
  const calculatedTotal = populated.reduce((sum, item) => {
    if (item.artwork) {
      return sum + item.artwork.price * item.qty;
    }
    return sum;
  }, 0);

  setTotal(calculatedTotal);
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

  const updateQuantity = async (artworkId: string, newQty: number) => {
    if (newQty < 1) return;
    
    try {
      const response = await cartService.updateCartItem(artworkId, newQty);
      if (response.success) {
        setCart(response.cart || null);
        setTotal(response.total || 0);
        
        // Update populated items
        setPopulatedItems(prev => 
          prev.map(item => 
            item.artworkId === artworkId 
              ? { ...item, qty: newQty }
              : item
          )
        );
      }
    } catch (error) {
      console.error('Error updating quantity:', error);
      toast.error('Failed to update quantity');
    }
  };

  const removeItem = async (artworkId: string) => {
    try {
      const response = await cartService.removeFromCart(artworkId);
      if (response.success) {
        setCart(response.cart || null);
        setTotal(response.total || 0);
        
        // Remove from populated items
        setPopulatedItems(prev => 
          prev.filter(item => item.artworkId !== artworkId)
        );
        
        toast.success('Item removed from cart');
      }
    } catch (error) {
      console.error('Error removing item:', error);
      toast.error('Failed to remove item');
    }
  };

 const handleCheckout = async () => {
    if (!cart || cart.items.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    try {
      setProcessingPayment(true);
      
      const orderResponse = await cartService.createOrderFromCart();
      
      if (!orderResponse.success || !orderResponse.created || orderResponse.created.length === 0) {
        toast.error(orderResponse.message || 'Failed to create order');
        return;
      }

      // Process payments for each seller group sequentially
      let allPaymentsSuccessful = true;
      for (let i = 0; i < orderResponse.created.length; i++) {
        const orderGroup = orderResponse.created[i];
        const { razorpayOrder, orderId } = orderGroup;
        
        if (!razorpayOrder) {
          toast.error(`Failed to initialize payment for order ${orderId}`);
          allPaymentsSuccessful = false;
          continue;
        }
        
        // Wait for user to complete this payment before opening next
        const paymentPromise = new Promise<void>((resolve, reject) => {
          const options = {
            key: import.meta.env.VITE_RAZORPAY_KEY_ID || 'your_razorpay_key_id',
            amount: razorpayOrder.amount,
            currency: razorpayOrder.currency,
            name: `Artisan Marketplace - Order ${orderId}`,
            description: `Payment for order ${orderId}`,
            order_id: razorpayOrder.id,
            handler: async function (response: any) {
              try {
                const verifyResponse = await cartService.verifyPayment({
                  razorpayOrderId: response.razorpay_order_id,
                  razorpayPaymentId: response.razorpay_payment_id,
                  razorpaySignature: response.razorpay_signature,
                  orderId: orderId // Pass orderId for verification
                });

                if (verifyResponse.success) {
                  toast.success(`Payment successful for order ${orderId}!`);
                  resolve();
                } else {
                  toast.error(`Payment verification failed for order ${orderId}`);
                  reject(new Error(`Payment verification failed for order ${orderId}`));
                }
              } catch (error) {
                console.error('Payment verification error:', error);
                toast.error(`Payment verification failed for order ${orderId}`);
                reject(error);
              }
            },
            modal: {
              ondismiss: function() {
                // User closed the payment modal without completing
                toast.error(`Payment cancelled for order ${orderId}`);
                reject(new Error(`Payment cancelled for order ${orderId}`));
              }
            },
            prefill: {
              name: 'Customer Name',
              email: 'customer@example.com',
              contact: '9999999999',
            },
            theme: {
              color: '#3B82F6',
            },
          };

          if (window.Razorpay) {
            const razorpay = new window.Razorpay(options);
            razorpay.open();
          } else {
            toast.error('Payment gateway not loaded. Please refresh and try again.');
            reject(new Error('Payment gateway not loaded'));
          }
        });

        try {
          // Wait for this payment to complete before proceeding to next
          await paymentPromise;
          
          // Small delay to ensure UI updates
          await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
          console.error(`Error processing payment for order ${orderId}:`, error);
          allPaymentsSuccessful = false;
          // Don't break the loop, continue with next payment
          // But you might want to ask user if they want to continue
          const continueAnyway = window.confirm(
            `Payment failed for order ${orderId}. Continue with remaining payments?`
          );
          if (!continueAnyway) {
            break;
          }
        }
      }

      // Reload cart and redirect if all payments were successful
      if (allPaymentsSuccessful) {
        toast.success('All payments completed successfully!');
        await loadCart();
        setTimeout(() => {
          window.location.href = '/orders';
        }, 1000);
      } else {
        toast.warning('Some payments may have failed. Please check your orders.');
        await loadCart(); // Reload to show current status
      }
      
    } catch (error: any) {
      console.error('Checkout error:', error);
      toast.error(error.response?.data?.message || 'Failed to process checkout');
    } finally {
      setProcessingPayment(false);
    }
  };

  if (loading) {
    return <Loader text="Loading your cart..." />;
  }

  if (!populatedItems || populatedItems.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <EmptyState
            icon={ShoppingCart}
            title="Your Cart is Empty"
            description="Add some amazing products to your cart to get started"
            action={{
              label: "Continue Shopping",
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
        <div className="flex items-center gap-4 mb-8">
          <Button 
            variant="ghost" 
            onClick={() => window.history.back()}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Shopping Cart</h1>
            <p className="text-muted-foreground">
              {populatedItems.length} {populatedItems.length === 1 ? 'item' : 'items'} in your cart
            </p>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            {populatedItems.map((item, index) => {
              if (!item.artwork) {
                return (
                  <Card key={item.artworkId || index}>
                    <CardContent className="p-6">
                      <div className="text-center py-4">
                        <p className="text-muted-foreground">Item no longer available</p>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="mt-2"
                          onClick={() => removeItem(item.artworkId)}
                        >
                          Remove
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              }

              const artwork = item.artwork;
              
              return (
                <Card key={artwork._id}>
                  <CardContent className="p-6">
                    <div className="flex gap-4">
                      <img
                        src={artwork.media?.[0]?.url || '/placeholder.svg'}
                        alt={artwork.title}
                        className="w-20 h-20 object-cover rounded-lg"
                      />
                      
                      <div className="flex-1">
                        <h3 className="font-semibold mb-2">{artwork.title}</h3>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => updateQuantity(artwork._id, item.qty - 1)}
                              disabled={item.qty <= 1}
                            >
                              <Minus className="w-4 h-4" />
                            </Button>
                            <Input
                              type="number"
                              value={item.qty}
                              onChange={(e) => {
                                const newQty = parseInt(e.target.value);
                                if (newQty > 0) {
                                  updateQuantity(artwork._id, newQty);
                                }
                              }}
                              className="w-16 text-center"
                              min="1"
                              max={artwork.quantity}
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => updateQuantity(artwork._id, item.qty + 1)}
                              disabled={item.qty >= artwork.quantity}
                            >
                              <Plus className="w-4 h-4" />
                            </Button>
                          </div>
                          
                          <div className="flex items-center gap-4">
                            <span className="font-semibold">
                              {getCurrencySymbol(artwork.currency)}
                              {(artwork.price * item.qty).toFixed(2)}
                            </span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeItem(artwork._id)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        
                        <div className="text-sm text-muted-foreground mt-2">
                          {artwork.quantity} available
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Subtotal ({populatedItems.length} items)</span>
                    <span>₹{total.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Shipping</span>
                    <span>Free</span>
                  </div>
                  <div className="border-t pt-2">
                    <div className="flex justify-between font-semibold">
                      <span>Total</span>
                      <span>₹{total.toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                <Button
                  onClick={handleCheckout}
                  disabled={processingPayment}
                  className="w-full btn-gradient"
                  size="lg"
                >
                  {processingPayment ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Processing...
                    </>
                  ) : (
                    <>
                      <CreditCard className="w-4 h-4 mr-2" />
                      Proceed to Payment
                    </>
                  )}
                </Button>

                <div className="text-xs text-muted-foreground text-center">
                  Secure payment powered by Razorpay
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CartPage;