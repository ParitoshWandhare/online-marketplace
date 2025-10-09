import apiClient from '@/lib/axios';

export interface Media {
  url: string;
  type: 'image' | 'video';
  sizeBytes?: number;
  storageKey?: string;
}

export interface Artwork {
  _id: string;
  artistId: {
    _id: string;
    name: string;
    email: string;
    avatarUrl?: string;
  };
  title: string;
  description?: string;
  media: Media[];
  price: number;
  currency: string;
  quantity: number;
  status: 'draft' | 'published' | 'removed' | 'out_of_stock';
  likeCount: number;
  tags?: string[]; 
  createdAt: string;
  updatedAt: string;
}

export interface CreateArtworkPayload {
  title: string;
  description?: string;
  price: number;
  currency?: string;
  quantity?: number;
  status?: string;
  media?: FileList;
}

export interface UpdateArtworkPayload {
  title?: string;
  description?: string;
  price?: number;
  currency?: string;
  quantity?: number;
  status?: 'draft' | 'published' | 'out_of_stock';
}

export interface ArtworkResponse {
  success: boolean;
  message: string;
  artwork?: Artwork;
  artworks?: Artwork[];
  count?: number;
}

export const artworkService = {
  async getAllArtworks(): Promise<ArtworkResponse> {
    const response = await apiClient.get('/artworks');
    return response.data;
  },

  async getMyArtworks(): Promise<ArtworkResponse> {
    const response = await apiClient.get('/artworks/me/my-artworks');
    return response.data;
  },

  async getArtworkById(id: string): Promise<ArtworkResponse> {
    const response = await apiClient.get(`/artworks/${id}`);
    return response.data;
  },

  async createArtwork(payload: CreateArtworkPayload): Promise<ArtworkResponse> {
    const formData = new FormData();
    
    formData.append('title', payload.title);
    if (payload.description) formData.append('description', payload.description);
    formData.append('price', payload.price.toString());
    if (payload.currency) formData.append('currency', payload.currency);
    if (payload.quantity) formData.append('quantity', payload.quantity.toString());
    if (payload.status) formData.append('status', payload.status);
    
    if (payload.media && payload.media.length > 0) {
      Array.from(payload.media).forEach((file) => {
        formData.append('media', file);
      });
    }

    const response = await apiClient.post('/artworks', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async deleteArtwork(id: string): Promise<ArtworkResponse> {
    const response = await apiClient.delete(`/artworks/${id}`);
    return response.data;
  },

  async updateArtwork(id: string, payload: UpdateArtworkPayload): Promise<ArtworkResponse> {
    const response = await apiClient.put(`/artworks/${id}`, payload);
    return response.data;
  },

  async getArtworksByArtist(artistId: string): Promise<ArtworkResponse> {
    const response = await apiClient.get(`/artworks/artist/${artistId}`);
    return response.data;
  },

  async restockArtwork(id: string, quantity: number): Promise<ArtworkResponse> {
    const response = await apiClient.patch(`/artworks/${id}/restock`, { quantity });
    return response.data;
  },
};