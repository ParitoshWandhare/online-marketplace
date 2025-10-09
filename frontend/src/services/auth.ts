import apiClient from '@/lib/axios';

export interface User {
  _id: string;
  id?: string;
  name: string;
  email: string;
  phone: string;
  bio?: string;
  avatarUrl?: string;
  region?: string;
  lastSeen?: string;
  likes?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupPayload {
  name: string;
  phone: string;
  email: string;
  password: string;
  confirmPassword: string;
  bio?: string;
  avatarUrl?: string;
  otp: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  token: string;
  user: User;
}

export interface SignupResponse {
  success: boolean;
  message: string;
  user: {
    id: string;
    name: string;
    email: string;
    phone: string;
  };
}

export interface SendOtpPayload {
  email: string;
}

export interface SendOtpResponse {
  success: boolean;
  message: string;
  email: string;
}

export const authService = {
  async sendOtp(payload: SendOtpPayload): Promise<SendOtpResponse> {
    const response = await apiClient.post('/auth/send-otp', payload);
    return response.data;
  },

  async signup(payload: SignupPayload): Promise<SignupResponse> {
    const response = await apiClient.post('/auth/signup', payload);
    return response.data;
  },

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  async getProfile(): Promise<{ success: boolean; message: string; user: User }> {
    const response = await apiClient.get('/user/me');
    return response.data;
  },
};