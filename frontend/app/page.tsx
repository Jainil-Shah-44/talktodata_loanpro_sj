import { Button, Container, Text, Title, Group, Paper, Stack } from '@mantine/core';
import { IconDatabase, IconChartBar, IconCheck } from '@tabler/icons-react';
import Link from 'next/link';

export default function Home() {
  return (
    <Container size="lg" py="xl">
      <Paper p="xl" radius="md" withBorder>
        <Title order={1} mb="xl" ta="center">TalkToData LoanPro</Title>
        <Text size="lg" mb="xl" ta="center">
          Loan Portfolio Validation and Analysis System
        </Text>

        <Stack gap="md" mb="xl">
          <Group justify="center" gap="xl">
            <Paper p="md" withBorder radius="md" style={{ width: '200px', textAlign: 'center' }}>
              <IconDatabase size={48} stroke={1.5} style={{ margin: '0 auto 10px' }} />
              <Title order={4}>Data Upload</Title>
              <Text size="sm" c="dimmed">Upload and manage loan portfolio data</Text>
            </Paper>
            
            <Paper p="md" withBorder radius="md" style={{ width: '200px', textAlign: 'center' }}>
              <IconCheck size={48} stroke={1.5} style={{ margin: '0 auto 10px' }} />
              <Title order={4}>Validation</Title>
              <Text size="sm" c="dimmed">Validate data against business rules</Text>
            </Paper>
            
            <Paper p="md" withBorder radius="md" style={{ width: '200px', textAlign: 'center' }}>
              <IconChartBar size={48} stroke={1.5} style={{ margin: '0 auto 10px' }} />
              <Title order={4}>Summary</Title>
              <Text size="sm" c="dimmed">Generate dynamic summary reports</Text>
            </Paper>
          </Group>
        </Stack>
        
        <Group justify="center">
          <Button component={Link} href="/login" size="lg">
            Get Started
          </Button>
        </Group>
      </Paper>
    </Container>
  );
}
