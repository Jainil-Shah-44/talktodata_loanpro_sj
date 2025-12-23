'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { 
  Container, Title, Text, Group, Button, TextInput, 
  Paper, Stack, Avatar, Loader, Card, ScrollArea,
  Code, Center, Select, Table
} from '@mantine/core';
import { IconSend, IconRobot, IconUser, IconDatabase, IconRefresh } from '@tabler/icons-react';
import { useDatasets } from '@/hooks/useDatasets';
import { useDataChat, ChatMessage } from '@/hooks/useDataChat';
import { useUserStore } from '@/src/store/userStore';

export default function Talk2DataPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const datasetId = searchParams.get('dataset');
  const { datasets, loading: datasetsLoading } = useDatasets();
  const { messages, loading, error, sendMessage, clearChat } = useDataChat(datasetId);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const user = useUserStore((state) => state.user);
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated || !user) {
      router.push('/login');
    }
  }, [isAuthenticated, user, router]);

  // Redirect to dataset selection if no dataset is selected
  useEffect(() => {
    if (!datasetId && datasets.length > 0) {
      router.push(`/dashboard/talk2data?dataset=${datasets[0].id}`);
    }
  }, [datasetId, datasets, router]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const currentDataset = datasets.find(d => d.id === datasetId) || (datasets.length > 0 ? datasets[0] : null);

  const handleSendMessage = () => {
    if (inputValue.trim() && !loading) {
      sendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Format the message content with SQL highlighting and query results if present
  const formatMessageContent = (message: ChatMessage) => {
    if (message.role === 'user') {
      return <Text>{message.content}</Text>;
    }

    // For assistant messages
    let content = message.content;
    
    // If there are query results with a table format in the content, remove that too
    // as we'll display it in a proper table component
    if (message.queryResults?.rows && message.queryResults.rows.length > 0) {
      // Remove the Results section from the content
      content = content.replace(/\n\nResults:[\s\S]*$/g, '');
    }
    
    return (
      <Stack gap="md">
        <Text>{content}</Text>
        
        {message.queryResults?.rows && message.queryResults.rows.length > 0 && (
          <Paper withBorder p="md">
            <Text size="sm" fw={500} mb="xs">Query Results:</Text>
            <Text size="xs" c="dimmed" mb="sm">Found {message.queryResults.rows.length} record(s)</Text>
            
            <ScrollArea h={Math.min(300, 50 + message.queryResults.rows.length * 35)}>
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    {message.queryResults.columns?.map((column, index) => (
                      <Table.Th key={index}>{column}</Table.Th>
                    ))}
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {message.queryResults.rows.map((row, rowIndex) => (
                    <Table.Tr key={rowIndex}>
                      {message.queryResults?.columns?.map((column, colIndex) => (
                        <Table.Td key={colIndex}>
                          {typeof row[column] === 'number' 
                            ? Number(row[column]).toLocaleString('en-IN')
                            : String(row[column] || '')}
                        </Table.Td>
                      ))}
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </ScrollArea>
          </Paper>
        )}
        
        {message.queryResults?.error && (
          <Paper withBorder p="xs" bg="red.1">
            <Text size="sm" fw={500} c="red.8">Query Error:</Text>
            <Text size="sm" c="red.8">{message.queryResults.error}</Text>
          </Paper>
        )}
      </Stack>
    );
  };

  if (datasetsLoading) {
    return (
      <Container size="xl" py="md">
        <Center h={400}>
          <Loader size="lg" />
        </Center>
      </Container>
    );
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>Talk2Data</Title>
        <Button 
          leftSection={<IconRefresh size="1rem" />} 
          variant="light" 
          onClick={clearChat}
        >
          New Chat
        </Button>
      </Group>

      {/* Dataset Selection Card */}
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
          
          <Select
            placeholder="Select Dataset"
            data={datasets.map(d => ({ value: d.id, label: d.name }))}
            value={datasetId || ''}
            onChange={(value: string | null) => {
              if (value) {
                // Clear chat when changing datasets
                clearChat();
                router.push(`/dashboard/talk2data?dataset=${value}`);
              }
            }}
            style={{ minWidth: '200px' }}
          />
        </Group>
      </Card>

      {/* Chat Area */}
      <Paper withBorder p="md" radius="md" mb="md">
        <ScrollArea h={400} mb="md">
          {messages.length === 0 ? (
            <Center h={350}>
              <Stack align="center" gap="md">
                <IconRobot size="3rem" stroke={1} color="#228be6" />
                <Title order={3}>Talk to Your Loan Data</Title>
                <Text c="dimmed" ta="center" maw={500}>
                  Chat with your loan portfolio data in plain English. Ask questions like:
                </Text>
                <Stack gap="xs" maw={450}>
                  <Paper withBorder p="xs" bg="blue.0" radius="md">
                    <Text size="sm" fw={500}>"How many loans do we have in each state?"</Text>
                  </Paper>
                  <Paper withBorder p="xs" bg="blue.0" radius="md">
                    <Text size="sm" fw={500}>"What's the average principal amount for loans with DPD over 90?"</Text>
                  </Paper>
                  <Paper withBorder p="xs" bg="blue.0" radius="md">
                    <Text size="sm" fw={500}>"Show me collection rates by product type"</Text>
                  </Paper>
                </Stack>
              </Stack>
            </Center>
          ) : (
            <Stack gap="md">
              {messages.map((message) => (
                <Group 
                  key={message.id} 
                  align="flex-start"
                  gap="sm"
                  style={{ 
                    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                    marginLeft: message.role === 'user' ? 'auto' : 0,
                    marginRight: message.role === 'assistant' ? 'auto' : 0,
                    maxWidth: '80%'
                  }}
                >
                  {message.role === 'assistant' && (
                    <Avatar color="blue" radius="xl">
                      <IconRobot size="1.5rem" />
                    </Avatar>
                  )}
                  
                  <Paper 
                    p="sm" 
                    radius="md" 
                    bg={message.role === 'user' ? 'blue.1' : 'gray.0'}
                    style={{ 
                      maxWidth: '100%',
                      wordBreak: 'break-word'
                    }}
                  >
                    {formatMessageContent(message)}
                  </Paper>
                  
                  {message.role === 'user' && (
                    <Avatar color="blue" radius="xl">
                      <IconUser size="1.5rem" />
                    </Avatar>
                  )}
                </Group>
              ))}
              <div ref={messagesEndRef} />
            </Stack>
          )}
        </ScrollArea>
        
        {error && (
          <Paper p="xs" mb="md" bg="red.1" c="red.8">
            <Text size="sm">{error}</Text>
          </Paper>
        )}
        
        <Group gap="xs">
          <TextInput
            placeholder="Ask a question about your loan data..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={loading}
            style={{ flex: 1 }}
          />
          <Button 
            onClick={handleSendMessage} 
            loading={loading}
            disabled={!inputValue.trim()}
            leftSection={<IconSend size="1rem" />}
          >
            Send
          </Button>
        </Group>
      </Paper>
    </Container>
  );
}
