'use client';

import { Button, Container, Text, Title } from '@mantine/core';

export default function TestPage() {
  return (
    <Container size="md" py="xl">
      <Title order={1} mb="md">TalkToData LoanPro Test Page</Title>
      <Text mb="lg">
        This is a simple test page to verify that the Mantine UI components are working correctly.
      </Text>
      <Button>Test Button</Button>
    </Container>
  );
}
