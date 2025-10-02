import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RecipeSearchResponse {
  query: string;
  response: string;
  total_results: number;
}

export interface AgentChatResponse {
  response: string;
  sources_used: string[];
}

export const searchRecipes = async (query: string): Promise<RecipeSearchResponse> => {
  const response = await axios.get(`${API_BASE_URL}/chat-search/${encodeURIComponent(query)}`);
  return response.data;
};

export const agentChat = async (message: string): Promise<AgentChatResponse> => {
  const response = await axios.post(`${API_BASE_URL}/agent-chat`, {
    message: message
  });
  return response.data;
};

export const clearAgentMemory = async (): Promise<void> => {
  await axios.post(`${API_BASE_URL}/agent-chat/clear`);
};

export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};