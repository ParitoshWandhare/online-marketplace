import apiClient from '@/lib/axios';

export interface CartItem {
  artworkId: string | {
    _id: string;
    title: string;
    price: number;
    currency: string;
    quantity: number;
    status: string;
  };
  qty: number;
}

// Full cart document
export interface Cart {
  _id: string;
  userId: string;
  items: CartItem[];
  createdAt: string;
  updatedAt: string;
  __v?: number;
}

// Response shape from API
export interface CartResponse {
  success: boolean;
  message?: string;
  cart?: Cart;
  total?: number;
}

// Order response when creating from cart
export interface CreateOrderResponse {
  success: boolean;
  message?: string;
  created?: Array<{
    orderId: string;  // Added orderId for frontend reference
    sellerId: string;
    order: any;
    razorpayOrder: {
      id: string;
      amount: number;
      currency: string;
    };
  }>;
}

export interface VerifyPaymentPayload {
  razorpayOrderId: string;
  razorpayPaymentId: string;
  razorpaySignature: string;
  orderId: string;  // Added orderId parameter
}

export interface VerifyPaymentResponse {
  success: boolean;
  message?: string;
  order?: any;
}

export const cartService = {
  async addToCart(artworkId: string, qty: number = 1): Promise<CartResponse> {
    const response = await apiClient.post('/cart/add', { artworkId, qty });
    return response.data;
  },

  async getCart(): Promise<CartResponse> {
    const response = await apiClient.get('/cart');
    return response.data;
  },

  async updateCartItem(artworkId: string, qty: number): Promise<CartResponse> {
    const response = await apiClient.put('/cart/update', { artworkId, qty });
    return response.data;
  },

  async removeFromCart(artworkId: string): Promise<CartResponse> {
    const response = await apiClient.delete(`/cart/remove/${artworkId}`);
    return response.data;
  },

  async createOrderFromCart(): Promise<CreateOrderResponse> {
    const response = await apiClient.post('/cart/checkout');
    return response.data;
  },

  async verifyPayment(paymentData: VerifyPaymentPayload): Promise<VerifyPaymentResponse> {
    const response = await apiClient.post('/cart/verify', paymentData);
    return response.data;
  },

  // Direct order creation (for Buy Now)
  async createDirectOrder(items: Array<{ artworkId: string; qty: number }>): Promise<{
    success: boolean;
    order?: any;
    razorpayOrder?: {
      id: string;
      amount: number;
      currency: string;
    };
  }> {
    const response = await apiClient.post('/order/direct', items[0]);
    return response.data;
  },

  async verifyDirectPayment(paymentData: {
    razorpayOrderId: string;
    razorpayPaymentId: string;
    razorpaySignature: string;
  }): Promise<VerifyPaymentResponse> {
    const response = await apiClient.post('/order/verify', paymentData);
    return response.data;
  }
};