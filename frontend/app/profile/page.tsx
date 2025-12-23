'use client';

import { useState, useEffect } from 'react';
import { 
  Container, 
  Paper, 
  Title, 
  TextInput, 
  Button, 
  Group, 
  Avatar, 
  Text, 
  Divider,
  SimpleGrid,
  Card,
  Badge,
  Alert
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconCheck, IconUserCircle, IconMail, IconLock, IconArrowLeft } from '@tabler/icons-react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useUserStore } from '@/src/store/userStore';

interface ProfileFormValues {
  full_name: string;
  email: string;
  current_password?: string;
  new_password?: string;
  confirm_password?: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const user = useUserStore((state) => state.user);
  const setUser = useUserStore((state: any) => state.setUser);
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  const [loading, setLoading] = useState(false);
  const [changePassword, setChangePassword] = useState(false);

  const form = useForm<ProfileFormValues>({
    initialValues: {
      full_name: user?.full_name || '',
      email: user?.email || '',
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
      new_password: (value) => 
        changePassword && value.length < 6 ? 'Password should be at least 6 characters' : null,
      confirm_password: (value, values) => 
        changePassword && value !== values.new_password ? 'Passwords do not match' : null,
    },
  });

  useEffect(() => {
    if (!isAuthenticated || !user) {
      router.push('/login');
    }
  }, [isAuthenticated, user, router]);

  const handleSubmit = async (values: ProfileFormValues) => {
    try {
      setLoading(true);

      // In a real app, you would call an API to update the user profile
      // For now, we'll just update the user in the store
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));

      // Update user in store
      if (user) {
        setUser({
          ...user,
          full_name: values.full_name,
          email: values.email,
        });
      }

      notifications.show({
        title: 'Profile updated',
        message: 'Your profile has been updated successfully',
        color: 'green',
        icon: <IconCheck size="1rem" />,
      });

      if (changePassword) {
        notifications.show({
          title: 'Password changed',
          message: 'Your password has been changed successfully',
          color: 'green',
          icon: <IconCheck size="1rem" />,
        });
        setChangePassword(false);
        form.setValues({
          ...values,
          current_password: '',
          new_password: '',
          confirm_password: '',
        });
      }
    } catch (error) {
      notifications.show({
        title: 'Error',
        message: 'An error occurred while updating your profile',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <Container size="md" py="xl">
      <Group mb="lg">
        <Button 
          component={Link} 
          href="/dashboard" 
          variant="subtle" 
          leftSection={<IconArrowLeft size="1rem" />}
        >
          Back to Dashboard
        </Button>
      </Group>

      <SimpleGrid cols={{ base: 1, md: 3 }} spacing="md">
        <Card withBorder p="xl" radius="md">
          <Group justify="center" mb="md">
            <Avatar 
              size="xl" 
              color="blue" 
              radius="xl"
            >
              {user.full_name.charAt(0)}
            </Avatar>
          </Group>
          <Text ta="center" fz="lg" fw={500}>{user.full_name}</Text>
          <Text ta="center" c="dimmed" size="sm">{user.email}</Text>
          <Divider my="md" />
          <Group justify="center">
            <Badge color="blue">Admin</Badge>
          </Group>
          <Text size="xs" ta="center" mt="md" c="dimmed">
            Member since {new Date().toLocaleDateString()}
          </Text>
        </Card>

        <Card withBorder p="xl" radius="md" style={{ gridColumn: 'span 2' }}>
          <Title order={3} mb="md">Profile Settings</Title>
          <form onSubmit={form.onSubmit(handleSubmit)}>
            <TextInput
              label="Full Name"
              placeholder="Your full name"
              icon={<IconUserCircle size="1rem" />}
              required
              mb="md"
              {...form.getInputProps('full_name')}
            />
            
            <TextInput
              label="Email"
              placeholder="your@email.com"
              icon={<IconMail size="1rem" />}
              required
              mb="md"
              {...form.getInputProps('email')}
            />
            
            <Divider my="lg" label="Password Settings" labelPosition="center" />
            
            <Group mb="md">
              <Button 
                variant={changePassword ? "filled" : "outline"} 
                onClick={() => setChangePassword(!changePassword)}
                size="xs"
              >
                {changePassword ? "Cancel Password Change" : "Change Password"}
              </Button>
            </Group>
            
            {changePassword && (
              <>
                <TextInput
                  label="Current Password"
                  placeholder="Your current password"
                  type="password"
                  icon={<IconLock size="1rem" />}
                  required={changePassword}
                  mb="md"
                  {...form.getInputProps('current_password')}
                />
                
                <TextInput
                  label="New Password"
                  placeholder="Your new password"
                  type="password"
                  icon={<IconLock size="1rem" />}
                  required={changePassword}
                  mb="md"
                  {...form.getInputProps('new_password')}
                />
                
                <TextInput
                  label="Confirm New Password"
                  placeholder="Confirm your new password"
                  type="password"
                  icon={<IconLock size="1rem" />}
                  required={changePassword}
                  mb="md"
                  {...form.getInputProps('confirm_password')}
                />
              </>
            )}
            
            <Group justify="flex-end" mt="xl">
              <Button type="submit" loading={loading}>
                Save Changes
              </Button>
            </Group>
          </form>
        </Card>
      </SimpleGrid>
    </Container>
  );
}
