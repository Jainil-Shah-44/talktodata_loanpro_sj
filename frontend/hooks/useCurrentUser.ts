'use client';

import { useState, useEffect } from 'react';
import { authService } from '@/src/api/services';

interface User {
  id: string;
  email: string;
  full_name?: string;
}

export function useCurrentUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        setLoading(true);
        
        // Check if we have an auth token
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        
        if (!token) {
          throw new Error('No authentication token found');
        }
        
        // Get user info from localStorage
        const userInfo = localStorage.getItem('user_info');
        if (userInfo) {
          try {
            const parsedUser = JSON.parse(userInfo);
            setUser(parsedUser);
          } catch (e) {
            console.error('Error parsing user info:', e);
            // Fallback to admin user
            setUser({
              id: '00000000-0000-0000-0000-000000000000',
              email: 'admin@example.com',
              full_name: 'Admin User'
            });
          }
        } else {
          // If user info is not in localStorage, use the admin user
          setUser({
            id: '00000000-0000-0000-0000-000000000000',
            email: 'admin@example.com',
            full_name: 'Admin User'
          });
        }
        
        setError(null);
      } catch (err: any) {
        console.error('Error fetching current user:', err);
        setError(err.message || 'Failed to fetch current user');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentUser();
  }, []);

  return { user, loading, error };
}
