import apiClient from './client';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name?: string;
    is_su:boolean //Added hvb @ 20/11/2025 to check if user admin user
  };
}

export const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  try {
    const response = await apiClient.post('/auth/login-json', credentials);
    return response.data;
  } catch (error: any) {
    console.error('Login error:', error);
    
    // Check if this is a database connection error
    if (error.response && error.response.status === 503) {
      throw new Error('Database connection error. Please try again later.');
    }
    
    // Check if this is an authentication error
    if (error.response && error.response.status === 401) {
      throw new Error('Invalid email or password.');
    }
    
    // For other errors
    throw error;
  }
};

export const mockLogin = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 800));
  
  // For development - mock successful login
  if (credentials.email && credentials.password.length >= 6) {
    return {
      access_token: 'mock_token_' + Date.now(),
      token_type: 'bearer',
      user: {
        id: '00000000-0000-0000-0000-000000000000',
        email: credentials.email,
        full_name: 'Demo User',
        is_su:false
      }
    };
  }
  
  // Mock authentication failure
  throw new Error('Invalid credentials');
};
