'use client';

import { useState, useEffect } from 'react';
import { Title, SimpleGrid, Card, Text, Group, Button, Center, Stack, Container, Paper, Alert, Badge, Select } from '@mantine/core';
import { IconDatabase, IconInfoCircle, IconAlertCircle } from '@tabler/icons-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useDatasets } from '@/hooks/useDatasets';
import { useUserStore } from '@/src/store/userStore';
import { ValidationChecklistWidget } from '@/components/ValidationChecklistWidget';

export default function ValidationDashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const datasetId = searchParams.get('dataset');
  const { datasets, loading: datasetsLoading, error: datasetsError } = useDatasets();
  const user = useUserStore((state) => state.user);
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  
  // Get the current dataset
  const currentDataset = datasets.find(d => d.id === datasetId) || (datasets.length > 0 ? datasets[0] : null);

  useEffect(() => {
    if (datasets.length > 0 && !datasetId) {
      // If no dataset is selected, redirect to the first one
      router.push(`/dashboard/validation?dataset=${datasets[0].id}`);
    }
  }, [datasets, datasetId, router]);

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
        <Title order={2}>Validation Dashboard</Title>
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
                  router.push(`/dashboard/validation?dataset=${value}`);
                }
              }}
              w={220}
            />
          </Group>
        </Group>
      </Card>

      {/* Checklist/Validation Widget */}
      {currentDataset && (
        <ValidationChecklistWidget datasetId={currentDataset.id} />
      )}
    </Container>
  );
}
