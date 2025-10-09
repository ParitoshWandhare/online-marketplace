import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Package, Search, Eye, MessageCircle } from 'lucide-react';
import { EmptyState } from '@/components/ui/EmptyState';
import { Loader } from '@/components/ui/Loader';
import { orderService, Order } from '@/services/order';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';

const OrderHistoryPage = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadBuyerOrders();
  }, []);

  const loadBuyerOrders = async () => {
    try {
      const response = await orderService.getMyOrders();
      if (response.success && response.orders) {
        setOrders(response.orders);
      }
    } catch (error) {
      console.error('Error loading orders:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load your orders.',
      });
    } finally {
      setLoading(false);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'created':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      case 'paid':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'shipped':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
      case 'out_for_delivery':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300';
      case 'delivered':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'cancelled':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'created': return 'Order Pending';
      case 'paid': return 'Payment Confirmed';
      case 'shipped': return 'Shipped';
      case 'out_for_delivery': return 'Out for Delivery';
      case 'delivered': return 'Delivered';
      case 'cancelled': return 'Cancelled';
      default: return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  const filteredOrders = orders.filter(order => {
    const matchesSearch = order.items.some(item => 
      item.titleCopy.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.sellerId?.name || '').toLowerCase().includes(searchQuery.toLowerCase())
    ) || order._id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return <Loader text="Loading your orders..." />;
  }

  if (orders.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <EmptyState
            icon={Package}
            title="No Orders Yet"
            description="Start shopping to see your order history here"
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
          <h1 className="text-3xl font-bold mb-2">Order History</h1>
          <p className="text-muted-foreground">
            Track and manage all your purchases
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search orders..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-48">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Orders</SelectItem>
                  <SelectItem value="created">Order Pending</SelectItem>
                  <SelectItem value="paid">Payment Confirmed</SelectItem>
                  <SelectItem value="shipped">Shipped</SelectItem>
                  <SelectItem value="out_for_delivery">Out for Delivery</SelectItem>
                  <SelectItem value="delivered">Delivered</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Orders List */}
        <div className="space-y-4">
          {filteredOrders.map((order) => (
            <Card key={order._id} className="card-hover">
              <CardContent className="pt-6">
                <div className="flex flex-col lg:flex-row gap-6">
                  {/* Order Image(s) */}
                  <div className="flex-shrink-0">
                    {order.items.length === 1 && order.items[0].artworkId?.media?.length ? (
                      <img
                        src={order.items[0].artworkId.media[0].url}
                        alt={order.items[0].titleCopy}
                        className="w-24 h-24 object-cover rounded-lg"
                      />
                    ) : (
                      <div className="w-24 h-24 bg-muted rounded-lg flex items-center justify-center">
                        <Package className="w-8 h-8 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground ml-1">
                          {order.items.length}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Order Details */}
                  <div className="flex-1 space-y-2">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                      <div>
                        <h3 className="font-semibold text-lg">
                          {order.items.length === 1 
                            ? order.items[0].titleCopy
                            : `${order.items.length} items`
                          }
                        </h3>
                        {order.items.length > 1 && (
                          <div className="text-sm text-muted-foreground">
                            {order.items.map((item) => item.titleCopy).join(', ')}
                          </div>
                        )}
                      </div>
                      <Badge className={getStatusColor(order.status)}>
                        {getStatusLabel(order.status)}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>Order #{order._id.slice(-8).toUpperCase()}</span>
                      <span>•</span>
                      <span>Ordered {format(new Date(order.createdAt), 'MMM dd, yyyy')}</span>
                    </div>

                    {/* Seller Info */}
                    <div className="flex items-center gap-3">
                      {order.items[0].sellerId && (
                        <>
                          <Avatar className="h-6 w-6">
                            <AvatarImage src={order.items[0].sellerId.avatarUrl} />
                            <AvatarFallback className="text-xs">
                              {order.items[0].sellerId.name.charAt(0)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-sm text-muted-foreground">
                            Sold by {order.items[0].sellerId.name}
                          </span>
                        </>
                      )}
                    </div>

                    <div className="text-lg font-semibold">
                      {getCurrencySymbol(order.currency)}{order.total.toFixed(2)}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-row lg:flex-col gap-2">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="flex items-center gap-2"
                          onClick={() => setSelectedOrder(order)}
                        >
                          <Eye className="w-4 h-4" />
                          View Details
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl" aria-describedby="">
                        <DialogHeader>
                          <DialogTitle>Order Details</DialogTitle>
                        </DialogHeader>
                        {selectedOrder && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <h4 className="font-semibold">Order Information</h4>
                                <p className="text-sm">Order ID: {selectedOrder._id}</p>
                                <p className="text-sm">Status: <Badge className={getStatusColor(selectedOrder.status)}>{getStatusLabel(selectedOrder.status)}</Badge></p>
                                <p className="text-sm">Date: {format(new Date(selectedOrder.createdAt), 'MMM dd, yyyy HH:mm')}</p>
                              </div>
                              <div>
                                <h4 className="font-semibold">Payment Information</h4>
                                <p className="text-sm">Total: {getCurrencySymbol(selectedOrder.currency)}{selectedOrder.total.toFixed(2)}</p>
                                <p className="text-sm">Currency: {selectedOrder.currency}</p>
                              </div>
                            </div>
                            <div>
                              <h4 className="font-semibold mb-2">Items Ordered</h4>
                              <div className="space-y-2">
                                {selectedOrder.items.map((item, index) => (
                                  <div key={index} className="flex justify-between items-center p-3 bg-muted rounded">
                                    <div className="flex items-center gap-3">
                                      <img
                                        src={item.artworkId?.media?.length ? item.artworkId.media[0].url : '/placeholder.svg'}
                                        alt={item.titleCopy}
                                        className="w-12 h-12 object-cover rounded"
                                      />
                                      <div>
                                        <p className="font-medium">{item.titleCopy}</p>
                                        <p className="text-sm text-muted-foreground">
                                          Quantity: {item.qty}
                                          {item.sellerId && ` • Sold by ${item.sellerId.name}`}
                                        </p>
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <p className="font-medium">
                                        {getCurrencySymbol(selectedOrder.currency)}{(item.unitPrice).toFixed(2)} each
                                      </p>
                                      <p className="text-sm text-muted-foreground">
                                        Subtotal: {getCurrencySymbol(selectedOrder.currency)}{(item.unitPrice * item.qty).toFixed(2)}
                                      </p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                              <div className="mt-4 pt-4 border-t">
                                <div className="flex justify-between items-center font-semibold">
                                  <span>Order Total:</span>
                                  <span>{getCurrencySymbol(selectedOrder.currency)}{selectedOrder.total.toFixed(2)}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredOrders.length === 0 && orders.length > 0 && (
          <EmptyState
            icon={Search}
            title="No Orders Found"
            description="Try adjusting your search or filter criteria"
          />
        )}
      </div>
    </div>
  );
};

export default OrderHistoryPage;