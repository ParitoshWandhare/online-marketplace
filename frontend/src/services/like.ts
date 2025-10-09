import apiClient from '@/lib/axios';
import { Artwork } from './artwork';

export interface LikeResponse {
  success: boolean;
  message: string;
}

export interface LikedArtworksResponse {
  success: boolean;
  count: number;
  artworks: Artwork[];
}

export const likeService = {
  async toggleLike(artworkId: string): Promise<LikeResponse> {
    const response = await apiClient.post(`/like/${artworkId}`);
    return response.data;
  },

  async getLikedArtworks(): Promise<LikedArtworksResponse> {
    const response = await apiClient.get('/like/my-likes');
    return response.data;
  },
};