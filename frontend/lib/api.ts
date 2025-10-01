import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RecipeSearchResponse {
  query: string;
  response: string;
  total_results: number;
}

export const searchRecipes = async (query: string): Promise<RecipeSearchResponse> => {
  const response = await axios.get(`${API_BASE_URL}/chat-search/${encodeURIComponent(query)}`);
  return response.data;
};

export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};