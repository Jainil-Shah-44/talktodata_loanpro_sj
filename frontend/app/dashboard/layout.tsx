'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  AppShell, 
  Burger, 
  Group, 
  NavLink, 
  Avatar, 
  Text, 
  UnstyledButton, 
  Menu, 
  rem,
  Title
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { 
  IconDashboard, 
  IconUpload, 
  IconChartBar, 
  IconLogout, 
  IconUser,
  IconChevronRight,
  IconMessageChatbot,
  IconFileAnalytics
} from '@tabler/icons-react';
import { useUserStore } from '@/src/store/userStore';

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [opened, { toggle }] = useDisclosure();
  const user = useUserStore((state) => state.user);
  const clearUser = useUserStore((state: any) => state.clearUser);
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    clearUser();
    router.push('/login');
  };

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 300, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Title order={3}>TalkToData LoanPro</Title>
          </Group>
          
          <Menu position="bottom-end" withArrow>
            <Menu.Target>
              <UnstyledButton>
                <Group>
                  <Avatar color="blue" radius="xl">
                    {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                  </Avatar>
                  <div>
                    <Text size="sm" fw={500}>
                      {user?.full_name || user?.email}
                    </Text>
                  </div>
                </Group>
              </UnstyledButton>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item 
                leftSection={<IconUser style={{ width: rem(14), height: rem(14) }} />}
                onClick={() => router.push('/profile')}
              >
                Profile
              </Menu.Item>
              <Menu.Item 
                leftSection={<IconLogout style={{ width: rem(14), height: rem(14) }} />}
                onClick={handleLogout}
              >
                Logout
              </Menu.Item>
            </Menu.Dropdown>
          </Menu>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <NavLink
          label="Dashboard"
          leftSection={<IconDashboard size="1rem" stroke={1.5} />}
          href="/dashboard"
        />
        <NavLink
          label="Dataset Selection"
          leftSection={<IconUpload size="1rem" stroke={1.5} />}
          href="/dashboard/datasets"
          rightSection={<IconChevronRight size="0.8rem" stroke={1.5} />}
        />
        <NavLink
          label="Validation Dashboard"
          leftSection={<IconDashboard size="1rem" stroke={1.5} />}
          href="/dashboard/validation"
        />
        <NavLink
          label="Summary Generation"
          leftSection={<IconChartBar size="1rem" stroke={1.5} />}
          href="/dashboard/summary"
        />
        <NavLink
          label="Talk2Data"
          leftSection={<IconMessageChatbot size="1rem" stroke={1.5} />}
          href="/dashboard/talk2data"
        />
        <NavLink
          label="Loan Pool Selection"
          leftSection={<IconFileAnalytics size="1rem" stroke={1.5} />}
          href="/dashboard/pool-selection"
        />
      </AppShell.Navbar>

      <AppShell.Main>
        {children}
      </AppShell.Main>
    </AppShell>
  );
}
