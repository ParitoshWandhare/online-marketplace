import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Eye } from 'lucide-react';
import { orderService, type Order } from '@/services/order';
import { useToast } from '@/hooks/use-toast';
import { Loader } from '@/components/ui/Loader';
import { format } from 'date-fns';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';

export const OrdersTable = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const loadSellerOrders = async () => {
      try {
        const response = await orderService.getSales();
        if (response.success && response.sales) {
          setOrders(
            response.sales.map((order: any) => ({
              ...order,
              items: order.items.map((item: any) => ({
                ...item,
                artworkId: item.artworkId
                  ? {
                      _id: item.artworkId._id || '',
                      title: item.artworkId.title || item.titleCopy || 'Unknown Product',
                      price: item.artworkId.price || item.unitPrice || 0,
                      currency: item.artworkId.currency || order.currency || 'USD',
                    }
                  : {
                      _id: '',
                      title: item.titleCopy || 'Unknown Product',
                      price: item.unitPrice || 0,
                      currency: order.currency || 'USD',
                    },
              })),
            }))
          );
        }
      } catch (error) {
        console.error('Error loading orders:', error);
        toast({
          variant: 'destructive',
          title: 'Error',
          description: 'Failed to load orders.',
        });
      } finally {
        setLoading(false);
      }
    };

    loadSellerOrders();
  }, [toast]);

  const getCurrencySymbol = (currency: string) => {
    const symbols: { [key: string]: string } = {
      INR: '₹',
      USD: '$',
      EUR: '€',
      GBP: '£',
    };
    return symbols[currency] || currency;
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'default';
      case 'shipped':
      case 'out_for_delivery':
        return 'secondary';
      case 'paid':
      case 'created':
        return 'outline';
      case 'pending':
      case 'failed':
      case 'cancelled':
        return 'destructive';
      default:
        return 'secondary';
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
      case 'pending': return 'Pending';
      case 'failed': return 'Failed';
      default: return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  const handleStatusChange = async (
    orderId: string,
    artworkId: string,
    newStatus: Order['status']
  ) => {
    try {
      setUpdating(orderId);
      const response = await orderService.updateOrderStatus(orderId, {
        artworkId,
        status: newStatus,
      });

      if (response.success && response.order) {
        setOrders((prev) =>
          prev.map((o) =>
            o._id === orderId ? { ...o, status: newStatus } : o
          )
        );
        toast({
          title: 'Success',
          description: `Order status updated to ${newStatus}.`,
        });
      } else {
        toast({
          variant: 'destructive',
          title: 'Error',
          description: response.message || 'Failed to update status.',
        });
      }
    } catch (error) {
      console.error('Error updating status:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to update order status.',
      });
    } finally {
      setUpdating(null);
    }
  };

  if (loading) {
    return <Loader text="Loading orders..." />;
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Order ID</TableHead>
            <TableHead>Buyer</TableHead>
            <TableHead>Items</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                No orders found. Your orders will appear here when customers purchase your items.
              </TableCell>
            </TableRow>
          ) : (
            orders.map((order) => (
              <TableRow key={order._id}>
                <TableCell className="font-medium">{order._id.slice(-8).toUpperCase()}</TableCell>
                <TableCell>{order.buyerId.name}</TableCell>
                <TableCell>{order.items.map((item) => item.titleCopy).join(', ')}</TableCell>
                <TableCell>
                  {getCurrencySymbol(order.currency)}
                  {order.total.toFixed(2)}
                </TableCell>
                <TableCell>
                  <Select
                    defaultValue={order.status}
                    onValueChange={(value) =>
                      handleStatusChange(
                        order._id,
                        order.items[0]?.artworkId?._id || '',
                        value as Order['status']
                      )
                    }
                    disabled={updating === order._id}
                  >
                    <SelectTrigger className="w-[160px]">
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="created">Created</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="paid">Paid</SelectItem>
                      <SelectItem value="shipped">Shipped</SelectItem>
                      <SelectItem value="out_for_delivery">Out for Delivery</SelectItem>
                      <SelectItem value="delivered">Delivered</SelectItem>
                      <SelectItem value="cancelled">Cancelled</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>{format(new Date(order.createdAt), 'MMM dd, yyyy')}</TableCell>
                <TableCell>
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedOrder(order)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Order Details</DialogTitle>
                      </DialogHeader>
                      {selectedOrder && (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <h4 className="font-semibold">Order Information</h4>
                              <p className="text-sm">Order ID: {selectedOrder._id}</p>
                              <p className="text-sm">
                                Status: <Badge variant={getStatusVariant(selectedOrder.status)}>
                                  {getStatusLabel(selectedOrder.status)}
                                </Badge>
                              </p>
                              <p className="text-sm">
                                Date: {format(new Date(selectedOrder.createdAt), 'MMM dd, yyyy HH:mm')}
                              </p>
                            </div>
                            <div>
                              <h4 className="font-semibold">Buyer Information</h4>
                              <p className="text-sm">Name: {selectedOrder.buyerId.name}</p>
                              <p className="text-sm">Email: {selectedOrder.buyerId.email}</p>
                            </div>
                          </div>
                          <div>
                            <h4 className="font-semibold mb-2">Items Ordered</h4>
                            <div className="space-y-2">
                              {selectedOrder.items.map((item, index) => (
                                <div key={index} className="flex justify-between items-center p-3 bg-muted rounded">
                                  <div>
                                    <p className="font-medium">{item.titleCopy}</p>
                                    <p className="text-sm text-muted-foreground">
                                      Quantity: {item.qty} • Price: {getCurrencySymbol(item.currency)}{item.unitPrice.toFixed(2)}
                                    </p>
                                    {item.sellerId && (
                                      <p className="text-sm text-muted-foreground">
                                        Sold by: {item.sellerId.name}
                                      </p>
                                    )}
                                  </div>
                                  <div className="text-right">
                                    <p className="font-medium">
                                      Subtotal: {getCurrencySymbol(item.currency)}{(item.unitPrice * item.qty).toFixed(2)}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                          <div className="mt-4 pt-4 border-t">
                            <div className="flex justify-between items-center font-semibold">
                              <span>Order Total:</span>
                              <span>{getCurrencySymbol(selectedOrder.currency)}{selectedOrder.total.toFixed(2)}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </DialogContent>
                  </Dialog>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </>
  );
};