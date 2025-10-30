//frontend/src/services/order.ts
import apiClient from '@/lib/axios';

interface PopulatedArtwork {
  _id: string;
  title: string;
  price: number;
  currency: string;
  media?: Array<{ url: string; type: string }>;
}

interface PopulatedUser {
  _id: string;
  name: string;
  email: string;
  avatarUrl?: string;
}

// Shipping address interface
interface ShippingAddress {
  fullName: string;
  phone: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  pincode: string;
  country?: string;
  landmark?: string;
}

export interface Order {
  _id: string;
  // This is a populated User object, not just an ID
  buyerId: PopulatedUser; 
  items: Array<{
    // This is a populated Artwork object, not just an ID
    artworkId: PopulatedArtwork;
    // This is a populated User object for the seller
    sellerId: PopulatedUser;
    qty: number;
    unitPrice: number;
    titleCopy: string;
    currency: string;
  }>;
  total: number;
  currency: string;
  status: 'created' | 'pending' | 'paid' | 'failed' | 'shipped' | 'out_for_delivery' | 'delivered' | 'cancelled';
  razorpayOrderId?: string;
  razorpayPaymentId?: string;
  razorpaySignature?: string;
  shippingAddress: ShippingAddress;  // Added as per Order model
  trackingNumber?: string;
  shippedAt?: string;
  deliveredAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface OrderResponse {
  success: boolean;
  message?: string;
  order?: Order;
  orders?: Order[];
  sales?: Order[];
  count?: number;
}

export const orderService = {
  // For sellers - get orders for their artworks (sales)
  async getSales(): Promise<OrderResponse> {
    const response = await apiClient.get('/order/my-sales');
    return response.data;
  },

  // For buyers - get their orders
  async getMyOrders(): Promise<OrderResponse> {
    const response = await apiClient.get('/order/my-orders');
    return response.data;
  },

  async getOrderById(id: string): Promise<OrderResponse> {
    const response = await apiClient.get(`/order/${id}`);
    return response.data;
  },

  async updateOrderStatus(orderId: string, updateData: { artworkId: string; status: string }): Promise<OrderResponse> {
    const response = await apiClient.put(`/order/${orderId}/status`, updateData);
    return response.data;
  },
};