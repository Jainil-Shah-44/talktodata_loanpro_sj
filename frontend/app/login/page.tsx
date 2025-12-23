'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { TextInput, PasswordInput, Button, Group, Box, Title, Text, Container, Paper, Alert } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconInfoCircle, IconAlertCircle } from '@tabler/icons-react';
import Link from 'next/link';
import { login, mockLogin, LoginCredentials } from '@/src/api/auth';
import { useUserStore } from '@/src/store/userStore';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [dbError, setDbError] = useState<string | null>(null);
  const [usedMockAuth, setUsedMockAuth] = useState(false);
  const router = useRouter();
  const setUser = useUserStore((state) => state.setUser);

  const form = useForm({
    initialValues: {
      email: 'admin@example.com',
      password: 'password123',
    },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
      password: (value) => (value.length >= 6 ? null : 'Password should be at least 6 characters'),
    },
  });

  const handleSubmit = async (values: LoginCredentials) => {
    try {
      setLoading(true);
      setApiError(null);
      setDbError(null);
      setUsedMockAuth(false);
      
      // Try to connect to the real backend first
      try {
        const response = await login(values);
        
        // Store the token in localStorage
        localStorage.setItem('auth_token', response.access_token);
        
        // Set user in global store
        // Mod hvb @ 20/11/2025 Set user from response
        /*const adminUser = {
          id: '00000000-0000-0000-0000-000000000000',
          email: 'admin@example.com',
          full_name: 'Admin User'
        };

        setUser(adminUser);*/

        //Added hvb @ 20/11/2025
        const loggedInuser = {
          id: response.user.id,
          email: response.user.email,
          full_name: response.user.full_name ?? 'User',
          is_su : response.user.is_su
        };

        setUser(loggedInuser);
        
        // Show success notification
        notifications.show({
          title: 'Login successful',
          message: 'You have been logged in successfully',
          color: 'green',
        });
        
        // Redirect to dashboard
        router.push('/dashboard');
      } catch (error: any) {
        console.log('Backend auth error:', error);
        
        // Check if this is a database connection error
        if (error.message && error.message.includes('Database connection error')) {
          setDbError('Database connection error. Cannot proceed with login.');
          notifications.show({
            title: 'Database Error',
            message: 'Cannot connect to the database. Please try again later.',
            color: 'red',
          });
          return; // Stop here, don't fall back to mock auth if DB is down
        }
        
        // For other errors, fall back to mock authentication for development
        setApiError('Backend authentication service unavailable');
        
        const mockResponse = await mockLogin(values);
        setUsedMockAuth(true);
        
        // Store the mock token
        localStorage.setItem('auth_token', mockResponse.access_token);
        
        // Set user in global store
        const adminUser = {
          id: '00000000-0000-0000-0000-000000000000',
          email: 'admin@example.com',
          full_name: 'Admin User',
          is_su:false
        };
        
        setUser(adminUser);
        
        // Show success notification with warning about mock auth
        notifications.show({
          title: 'Login successful (Development Mode)',
          message: 'Using mock authentication for development',
          color: 'blue',
        });
        
        // Redirect to dashboard
        router.push('/dashboard');
      }
    } catch (error: any) {
      // This will only happen if both real and mock auth fail
      notifications.show({
        title: 'Login failed',
        message: error.message || 'Invalid credentials',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size="xs" py="xl">
      <Paper radius="md" p="xl" withBorder>
        <Title order={2} ta="center" mt="md" mb={50}>
          Welcome to TalkToData LoanPro
        </Title>

        {dbError && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Database Error" color="red" mb="md">
            {dbError}
          </Alert>
        )}

        {apiError && !dbError && (
          <Alert icon={<IconInfoCircle size="1rem" />} title="Connection Notice" color="yellow" mb="md">
            {apiError}. Using mock authentication for development.
          </Alert>
        )}

        <form onSubmit={form.onSubmit(handleSubmit)}>
          <TextInput
            label="Email"
            placeholder="your@email.com"
            required
            {...form.getInputProps('email')}
          />
          <PasswordInput
            label="Password"
            placeholder="Your password"
            required
            mt="md"
            {...form.getInputProps('password')}
          />

          <Group justify="space-between" mt="lg">
            <Text size="sm" c="dimmed">
              Don&apos;t have an account?{' '}
              <Link href="#" style={{ textDecoration: 'none', color: 'blue' }}>
                Register
              </Link>
            </Text>
          </Group>

          <Button fullWidth mt="xl" type="submit" loading={loading} disabled={!!dbError}>
            Sign in
          </Button>
        </form>
      </Paper>
    </Container>
  );
}
