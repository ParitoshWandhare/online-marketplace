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
};