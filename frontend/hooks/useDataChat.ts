'use client';

import { useState } from 'react';
import apiClient from '@/src/api/client';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryResults?: {
    columns?: string[];
    rows?: Record<string, any>[];
    error?: string;
  };
}

export function useDataChat(datasetId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (message: string) => {
    if (!datasetId) {
      setError('No dataset selected');
      return;
    }

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post(`/datasets/${datasetId}/chat`, {
        query: message
      });

      const responseData = response.data;
      
      if (responseData.type === 'error') {
        setError(responseData.message);
        return;
      }

      // Add assistant message to chat
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseData.response,
        timestamp: new Date(),
        queryResults: responseData.query_results
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Error in chat:', err);
      setError(err.message || 'Failed to get a response');
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearChat
  };
}
