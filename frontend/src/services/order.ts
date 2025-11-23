import apiClient from '@/lib/axios';

// Interfaces for the populated documents from the backend
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

interface ShippingAddress {
  _id: string;
  label: 'Home' | 'Work' | 'Other';
  fullName: string;
  phone: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  landmark?: string;
  isDefault: boolean;
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
  // Reference to user's address by ID
  shippingAddressId: string;
  // Populated shipping address (added by backend)
  shippingAddress?: ShippingAddress | null;
  status: 'created' | 'pending' | 'paid' | 'failed' | 'shipped' | 'out_for_delivery' | 'delivered' | 'cancelled';
  razorpayOrderId?: string;
  razorpayPaymentId?: string;
  razorpaySignature?: string;
  trackingNumber?: string;
  shippedAt?: string;
  deliveredAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateOrderPayload {
  items: Array<{
    artworkId: string;
    sellerId: string;
    qty: number;
  }>;
  shippingAddressId: string;
}

export interface CreateDirectOrderPayload {
  artworkId: string;
  qty: number;
  shippingAddressId: string;
}

export interface VerifyPaymentPayload {
  razorpayOrderId: string;
  razorpayPaymentId: string;
  razorpaySignature: string;
}

export interface UpdateOrderStatusPayload {
  artworkId: string;
  status: 'created' | 'pending' | 'paid' | 'failed' | 'shipped' | 'out_for_delivery' | 'delivered' | 'cancelled';
  trackingNumber?: string;
}

export interface RazorpayOrder {
  id: string;
  entity: string;
  amount: number;
  amount_paid: number;
  amount_due: number;
  currency: string;
  receipt: string;
  status: string;
  attempts: number;
  created_at: number;
}

export interface OrderResponse {
  success: boolean;
  message?: string;
  order?: Order;
  orders?: Order[];
  sales?: Order[];
  count?: number;
}

export interface CreateOrderResponse {
  success: boolean;
  created: Array<{
    sellerId: string;
    order: Order;
    razorpayOrder: RazorpayOrder;
  }>;
}

export interface CreateDirectOrderResponse {
  success: boolean;
  order: Order;
  razorpayOrder: RazorpayOrder;
}

export const orderService = {
  // Create order with multiple items (multi-seller)
  async createOrder(payload: CreateOrderPayload): Promise<CreateOrderResponse> {
    const response = await apiClient.post('/order/create', payload);
    return response.data;
  },

  // Create direct order (single item, Buy Now)
  async createDirectOrder(payload: CreateDirectOrderPayload): Promise<CreateDirectOrderResponse> {
    const response = await apiClient.post('/order/direct', payload);
    return response.data;
  },

  // Verify payment after successful Razorpay payment
  async verifyPayment(payload: VerifyPaymentPayload): Promise<OrderResponse> {
    const response = await apiClient.post('/order/verify', payload);
    return response.data;
  },

  // For buyers - get their orders
  async getMyOrders(): Promise<OrderResponse> {
    const response = await apiClient.get('/order/my-orders');
    return response.data;
  },

  // For sellers - get orders for their artworks (sales)
  async getSales(): Promise<OrderResponse> {
    const response = await apiClient.get('/order/my-sales');
    return response.data;
  },

  // Update order status (seller only)
  async updateOrderStatus(orderId: string, updateData: UpdateOrderStatusPayload): Promise<OrderResponse> {
    const response = await apiClient.put(`/order/${orderId}/status`, updateData);
    return response.data;
  },
};