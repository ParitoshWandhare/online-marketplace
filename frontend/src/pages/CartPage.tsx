import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Minus, Plus, Trash2, ShoppingCart, ArrowLeft, CreditCard, MapPin, Plus as PlusIcon } from 'lucide-react';
import { cartService, type Cart } from '@/services/cart';
import { artworkService } from '@/services/artwork';
import { userService, Address } from '@/services/user';
import { orderService } from '@/services/order';
import { Loader } from '@/components/ui/Loader';
import { EmptyState } from '@/components/ui/EmptyState';
import { useToast } from '@/hooks/use-toast';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { AddAddressForm } from '@/components/forms/AddAddressForm';

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
    artistId: string;
  } | null;
  qty: number;
}

const CartPage = () => {
  const [cart, setCart] = useState<Cart | null>(null);
  const [populatedItems, setPopulatedItems] = useState<PopulatedCartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [total, setTotal] = useState(0);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [selectedAddressId, setSelectedAddressId] = useState<string>('');
  const [showAddressDialog, setShowAddressDialog] = useState(false);
  const [showAddAddressDialog, setShowAddAddressDialog] = useState(false);
  const { toast: hookToast } = useToast();

  useEffect(() => {
    loadCart();
    loadAddresses();
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

  const loadAddresses = async () => {
    try {
      const response = await userService.getAddresses();
      if (response.success) {
        setAddresses(response.addresses);
        // Set default address if available
        const defaultAddr = response.addresses.find(addr => addr.isDefault);
        if (defaultAddr) {
          setSelectedAddressId(defaultAddr._id);
        }
      }
    } catch (error) {
      console.error('Error loading addresses:', error);
    }
  };

  const loadCart = async () => {
    try {
      const response = await cartService.getCart();
      if (response.success && response.cart) {
        setCart(response.cart);
        setTotal(response.total || 0);
        
        if (response.cart.items && response.cart.items.length > 0) {
          await populateCartItems(response.cart.items);
        } else {
          setPopulatedItems([]);
        }
      } else {
        setCart({ _id: '', userId: '', items: [], createdAt: '', updatedAt: '' });
        setPopulatedItems([]);
        setTotal(0);
      }
    } catch (error) {
      console.error('Error loading cart:', error);
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
        let artworkId: string = '';
        if (typeof item.artworkId === 'string') {
          artworkId = item.artworkId;
        } else if (item.artworkId?._id) {
          artworkId = item.artworkId._id;
        } else if (item.artworkId?.$oid) {
          artworkId = item.artworkId.$oid;
        }

        let qty: number = item.qty;
        if (item.qty?.$numberInt) {
          qty = parseInt(item.qty.$numberInt, 10);
        }

        if (typeof item.artworkId === 'object' && item.artworkId._id) {
          populated.push({
            artworkId,
            artwork: item.artworkId,
            qty,
          });
        } else {
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

  const handleCheckout = async () => {
    if (!cart || cart.items.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    if (!selectedAddressId) {
      toast.error('Please select a shipping address');
      setShowAddressDialog(true);
      return;
    }

    try {
      setProcessingPayment(true);
      
      // Prepare items with seller info
      const orderItems = populatedItems
        .filter(item => item.artwork)
        .map(item => ({
          artworkId: item.artworkId,
          sellerId: item.artwork!.artistId,
          qty: item.qty
        }));

      // Create order with shipping address
      const orderResponse = await orderService.createOrder({
        items: orderItems,
        shippingAddressId: selectedAddressId
      });
      
      if (!orderResponse.success || !orderResponse.created || orderResponse.created.length === 0) {
        toast.error('Failed to create order');
        return;
      }

      // Process payments for each seller group sequentially
      let allPaymentsSuccessful = true;
      for (let i = 0; i < orderResponse.created.length; i++) {
        const orderGroup = orderResponse.created[i];
        const { razorpayOrder, order } = orderGroup;
        
        if (!razorpayOrder) {
          toast.error(`Failed to initialize payment for order ${order._id}`);
          allPaymentsSuccessful = false;
          continue;
        }
        
        const paymentPromise = new Promise<void>((resolve, reject) => {
          const options = {
            key: import.meta.env.VITE_RAZORPAY_KEY_ID || 'your_razorpay_key_id',
            amount: razorpayOrder.amount,
            currency: razorpayOrder.currency,
            name: 'Artisan Marketplace',
            description: `Payment for Order ${i + 1} of ${orderResponse.created.length}`,
            order_id: razorpayOrder.id,
            handler: async function (response: any) {
              try {
                const verifyResponse = await orderService.verifyPayment({
                  razorpayOrderId: response.razorpay_order_id,
                  razorpayPaymentId: response.razorpay_payment_id,
                  razorpaySignature: response.razorpay_signature
                });

                if (verifyResponse.success) {
                  toast.success(`Payment ${i + 1} successful!`);
                  resolve();
                } else {
                  toast.error(`Payment verification failed`);
                  reject(new Error('Payment verification failed'));
                }
              } catch (error) {
                console.error('Payment verification error:', error);
                toast.error('Payment verification failed');
                reject(error);
              }
            },
            modal: {
              ondismiss: function() {
                toast.error('Payment cancelled');
                reject(new Error('Payment cancelled'));
              }
            },
            prefill: {
              name: addresses.find(a => a._id === selectedAddressId)?.fullName || 'Customer',
              contact: addresses.find(a => a._id === selectedAddressId)?.phone || '9999999999',
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
          await paymentPromise;
          await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
          console.error(`Error processing payment:`, error);
          allPaymentsSuccessful = false;
          const continueAnyway = window.confirm(
            `Payment failed. Continue with remaining payments?`
          );
          if (!continueAnyway) {
            break;
          }
        }
      }

      if (allPaymentsSuccessful) {
        toast.success('All payments completed successfully!');
        await loadCart();
        setTimeout(() => {
          window.location.href = '/orders';
        }, 1000);
      } else {
        toast.warning('Some payments may have failed. Please check your orders.');
        await loadCart();
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

  const selectedAddress = addresses.find(a => a._id === selectedAddressId);

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
                {/* Shipping Address Section */}
                <div className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      Shipping Address
                    </h3>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setShowAddressDialog(true)}
                    >
                      Change
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
                      <p className="text-muted-foreground">Phone: {selectedAddress.phone}</p>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full"
                      onClick={() => setShowAddAddressDialog(true)}
                    >
                      <PlusIcon className="w-4 h-4 mr-2" />
                      Add Shipping Address
                    </Button>
                  )}
                </div>

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
                  disabled={processingPayment || !selectedAddressId}
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

      {/* Address Selection Dialog */}
      <Dialog open={showAddressDialog} onOpenChange={setShowAddressDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Select Shipping Address</DialogTitle>
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

export default CartPage;