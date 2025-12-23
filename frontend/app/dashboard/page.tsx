'use client';

import { useState, useEffect } from 'react';
import { Title, SimpleGrid, Card, Text, Group, Button, Center, Stack, Container, Paper, Alert, Badge, Select } from '@mantine/core';
import { IconUpload, IconDatabase, IconAlertCircle, IconCheck, IconChartBar, IconInfoCircle, IconUser } from '@tabler/icons-react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useDatasets } from '@/hooks/useDatasets';
import { useUserStore } from '@/src/store/userStore';

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const datasetId = searchParams.get('dataset');
  const { datasets, loading: datasetsLoading, error: datasetsError } = useDatasets();
  const user = useUserStore((state) => state.user);
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  
  // Get the current dataset
  const currentDataset = datasets.find(d => d.id === datasetId) || (datasets.length > 0 ? datasets[0] : null);

  if (datasetsLoading) {
    return (
      <Container size="xl" py="md">
        <Center h={400}>
          <Text>Loading data...</Text>
        </Center>
      </Container>
    );
  }

  if (!isAuthenticated || !user) {
    // Redirect to login if not authenticated
    router.push('/login');
    return null;
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>Loan Portfolio Dashboard</Title>
        <Button 
          leftSection={<IconUpload size="1rem" />}
          variant="outline"
          onClick={() => router.push('/dashboard/upload')}
        >
          Upload New Dataset
        </Button>
      </Group>

      {datasetsError && (
        <Alert icon={<IconInfoCircle size="1rem" />} title="Connection Error" color="yellow" mb="md">
          {datasetsError}. Using mock data for demonstration.
        </Alert>
      )}
      
      <Card withBorder p="md" radius="md" mb="lg">
        <Group justify="space-between">
          <Group>
            <IconDatabase size="1.5rem" stroke={1.5} />
            <div>
              <Text fw={500} size="lg">
                {currentDataset ? currentDataset.name : 'No Dataset Selected'}
              </Text>
              {currentDataset?.description && (
                <Text size="xs" c="dimmed">{currentDataset.description}</Text>
              )}
            </div>
          </Group>
          
          <Group>
            {currentDataset && (
              <Badge size="lg" color={currentDataset.status === 'validated' ? 'green' : 'blue'}>
                {currentDataset.status === 'validated' ? 'Validated' : 'Pending Validation'}
              </Badge>
            )}
            
            <Select
              placeholder="Change Dataset"
              data={datasets.map(d => ({ value: d.id, label: d.name }))}
              value={currentDataset?.id}
              onChange={(value) => {
                if (value) {
                  router.push(`/dashboard?dataset=${value}`);
                }
              }}
              w={220}
            />
          </Group>
        </Group>
      </Card>

      <Paper withBorder p="md" mb="lg">
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="lg">
          <Card withBorder p="md" radius="md">
            <Group justify="apart">
              <Text size="xs" c="dimmed" fw={700} tt="uppercase">Total Datasets</Text>
            </Group>
            <Group justify="apart" mt="xs">
              <Text size="xl" fw={700}>{datasets.length}</Text>
              <IconDatabase size="1.4rem" stroke={1.5} />
            </Group>
          </Card>
          
          <Card withBorder p="md" radius="md">
            <Group justify="apart">
              <Text size="xs" c="dimmed" fw={700} tt="uppercase">Total Records</Text>
            </Group>
            <Group justify="apart" mt="xs">
              <Text size="xl" fw={700}>
                {datasets.reduce((acc, dataset) => acc + (dataset.total_records || 0), 0)}
              </Text>
              <IconDatabase size="1.4rem" stroke={1.5} />
            </Group>
          </Card>

          <Card withBorder p="md" radius="md">
            <Group justify="apart">
              <Text size="xs" c="dimmed" fw={700} tt="uppercase">Validation Status</Text>
            </Group>
            <Group justify="apart" mt="xs">
              <Text size="xl" fw={700}>
                {datasets.filter(d => d.status === 'validated').length} / {datasets.length}
              </Text>
              {datasets.filter(d => d.status === 'validated').length === datasets.length ? (
                <IconCheck size="1.4rem" stroke={1.5} color="green" />
              ) : (
                <IconAlertCircle size="1.4rem" stroke={1.5} color="orange" />
              )}
            </Group>
          </Card>

          <Card withBorder p="md" radius="md">
            <Group justify="apart">
              <Text size="xs" c="dimmed" fw={700} tt="uppercase">Latest Upload</Text>
            </Group>
            <Group justify="apart" mt="xs">
              <Text size="xl" fw={700}>
                {datasets.length > 0 
                  ? new Date(datasets[0].upload_date).toLocaleDateString() 
                  : 'N/A'}
              </Text>
              <IconUpload size="1.4rem" stroke={1.5} />
            </Group>
          </Card>
        </SimpleGrid>
      </Paper>

      <Paper withBorder p="lg" mt="md">
        <Title order={3} mb="md">Loan Portfolio Overview</Title>
        <Text mb="lg">
          Welcome to the TalkToData LoanPro dashboard. Use the sidebar to navigate to different features:
        </Text>
        
        <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="lg">
          <Card withBorder p="md" radius="md">
            <Title order={4} mb="xs">Validation Dashboard</Title>
            <Text c="dimmed" size="sm" mb="md">
              View validation metrics and errors for your loan portfolio data
            </Text>
            <Button 
              fullWidth 
              mt="md" 
              variant="filled" 
              onClick={() => router.push(`/dashboard/validation?dataset=${currentDataset?.id}`)}
            >
              Go to Validation
            </Button>
          </Card>
          
          <Card withBorder p="md" radius="md">
            <Title order={4} mb="xs">Summary Generation</Title>
            <Text c="dimmed" size="sm" mb="md">
              Generate and customize summary reports with bucket configurations
            </Text>
            <Button 
              fullWidth 
              mt="md" 
              variant="filled" 
              onClick={() => router.push(`/dashboard/summary?dataset=${currentDataset?.id}`)}
            >
              Go to Summaries
            </Button>
          </Card>
          
          <Card withBorder p="md" radius="md">
            <Title order={4} mb="xs">Loan Records</Title>
            <Text c="dimmed" size="sm" mb="md">
              View and filter individual loan records in the selected dataset
            </Text>
            <Button 
              fullWidth 
              mt="md" 
              variant="filled" 
              onClick={() => router.push(`/dashboard/records?dataset=${currentDataset?.id}`)}
            >
              View Records
            </Button>
          </Card>
        </SimpleGrid>
      </Paper>
    </Container>
  );
}
