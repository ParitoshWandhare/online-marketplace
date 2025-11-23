import apiClient from '@/lib/axios';
import { User } from './auth';

export interface UpdateProfilePayload {
  name?: string;
  phone?: string;
  avatarUrl?: string;
  bio?: string;
  region?: string;
}

export interface UserResponse {
  success: boolean;
  message?: string;
  user: User;
}

export interface Address {
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
  createdAt: string;
  updatedAt: string;
}

export interface AddAddressPayload {
  label: 'Home' | 'Work' | 'Other';
  fullName: string;
  phone: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  state: string;
  pincode: string;
  country?: string;
  landmark?: string;
  isDefault?: boolean;
}

export interface UpdateAddressPayload {
  label?: 'Home' | 'Work' | 'Other';
  fullName?: string;
  phone?: string;
  addressLine1?: string;
  addressLine2?: string;
  city?: string;
  state?: string;
  pincode?: string;
  country?: string;
  landmark?: string;
  isDefault?: boolean;
}

export interface AddressesResponse {
  success: boolean;
  count: number;
  addresses: Address[];
}

export interface AddressResponse {
  success: boolean;
  message?: string;
  address: Address;
}

export const userService = {
  async getProfile(): Promise<UserResponse> {
    const response = await apiClient.get('/user/me');
    return response.data;
  },

  async updateProfile(payload: UpdateProfilePayload): Promise<UserResponse> {
    const response = await apiClient.put('/user/update', payload);
    return response.data;
  },

  async deleteAccount(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete('/user/delete');
    return response.data;
  },

  async getUserById(userId: string): Promise<UserResponse> {
    const response = await apiClient.get(`/users/${userId}`);
    return response.data;
  },

  // Get seller stats
  async getSellerStats(): Promise<{
    success: boolean;
    stats: {
      totalProducts: number;
      totalOrders: number;
      totalRevenue: number;
    };
  }> {
    const response = await apiClient.get('/user/stats');
    return response.data;
  },

  // Address Management
  async getAddresses(): Promise<AddressesResponse> {
    const response = await apiClient.get('/user/addresses');
    return response.data;
  },

  async getDefaultAddress(): Promise<AddressResponse> {
    const response = await apiClient.get('/user/addresses/default');
    return response.data;
  },

  async getAddressById(addressId: string): Promise<AddressResponse> {
    const response = await apiClient.get(`/user/addresses/${addressId}`);
    return response.data;
  },

  async addAddress(payload: AddAddressPayload): Promise<AddressResponse> {
    const response = await apiClient.post('/user/addresses', payload);
    return response.data;
  },

  async updateAddress(addressId: string, payload: UpdateAddressPayload): Promise<AddressResponse> {
    const response = await apiClient.put(`/user/addresses/${addressId}`, payload);
    return response.data;
  },

  async deleteAddress(addressId: string): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(`/user/addresses/${addressId}`);
    return response.data;
  },

  async setDefaultAddress(addressId: string): Promise<AddressResponse> {
    const response = await apiClient.patch(`/user/addresses/${addressId}/set-default`);
    return response.data;
  },
};