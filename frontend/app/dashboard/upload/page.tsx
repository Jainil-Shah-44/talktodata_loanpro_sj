'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Container,
  Title,
  Text,
  Button,
  Group,
  TextInput,
  Textarea,
  FileInput,
  Card,
  Alert,
  Stepper,
  rem,
  LoadingOverlay,
  Progress,
  Checkbox,
  Select,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconUpload, IconFile, IconAlertCircle, IconCheck, IconX } from '@tabler/icons-react';
import { datasetService } from '@/src/api/services';

//Added hvb @ 17/11/2025 for using new mapping config's
import { mappingService } from "@/src/api/mappingService";
import { MappingProfileSummary } from "@/src/types/mappings";
//commented hvb @ 18/11/2025 created wiz based model instead
import { ManageMappingModal } from "@/components/mapping/ManageMappingModal";
//import { ManageMappingModal } from "@/components/mapping/ManageMappingModalWizBased";


export default function UploadDatasetPage() {
  const router = useRouter();
  const [active, setActive] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Form data
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  
  // Validation states
  const [nameError, setNameError] = useState('');
  const [fileError, setFileError] = useState('');
  
  //Handle mapping selection, added hvb 
  const [useMappings, setMappingUse] = useState(false);
  const [mappingName, setMappingName] = useState('');
  const [modalOpen, setMappingModalOpen] = useState(false);

  //Added hvb @ 17/11/2025 for mapping soft-coding
  const [profiles, setProfiles] = useState<MappingProfileSummary[]>([]);
  const mappingSelectData = profiles.map((p) => ({ value: String(p.id), label: p.name }));
  useEffect(() => {
    loadProfiles();
  }, []);

  async function loadProfiles(): Promise<void> {
    const list = await mappingService.list();
    setProfiles(list);
  }

  const handleSubmit = async () => {
    // Validate form
    let isValid = true;
    
    if (!name.trim()) {
      setNameError('Dataset name is required');
      isValid = false;
    } else {
      setNameError('');
    }
    
    if (!file) {
      setFileError('Please select a file to upload');
      isValid = false;
    } else {
      setFileError('');
    }
    
    if (!isValid) return;
    
    // Proceed to confirmation step
    setActive(1);
  };
  
  const handleUpload = async () => {
    if (!file) return;
    
    setLoading(true);
    setError(null);
    setActive(2);
    
    let progressIntervalId: NodeJS.Timeout | null = null;
    
    try {
      // Create form data

      /*if(useMappings)
      {
        alert("Use mappings with mapping name : " + mappingName);
        return;
      }*/

      const formData = new FormData();
      formData.append('file', file);
      
      // Add metadata as JSON string in a separate field
      const metadata = {
        name,
        description,

        //Added hvb @ 19/10/25
        mapping:mappingName
      };
      formData.append('metadata', JSON.stringify(metadata));
      
      // Simulate upload progress
      progressIntervalId = setInterval(() => {
        setUploadProgress(prev => {
          const newProgress = prev + Math.random() * 10;
          return newProgress > 90 ? 90 : newProgress;
        });
      }, 500);
      
      // Upload the dataset, checkbox based ep selection added hvb
      //const response = await datasetService.uploadDataset(formData);
      const response = await (useMappings ? datasetService.uploadDatasetWithMapping(formData) : datasetService.uploadDataset(formData));
      
      if (progressIntervalId) {
        clearInterval(progressIntervalId);
      }
      setUploadProgress(100);
      
      // Show success notification
      notifications.show({
        title: 'Upload Successful',
        message: 'Your dataset has been uploaded successfully',
        color: 'green',
        icon: <IconCheck size="1.1rem" />,
      });
      
      // Move to success step
      setActive(3);
      
      // Redirect to dataset page after a short delay
      setTimeout(() => {
        router.push(`/dashboard/datasets`);
      }, 2000);
      
    } catch (err: any) {
      if (progressIntervalId) {
        clearInterval(progressIntervalId);
      }
      setUploadProgress(0);
      setError(err.message || 'Failed to upload dataset');
      setActive(1);
      
      // Show error notification
      notifications.show({
        title: 'Upload Failed',
        message: err.message || 'Failed to upload dataset',
        color: 'red',
        icon: <IconX size="1.1rem" />,
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleCancel = () => {
    router.push('/dashboard/datasets');
  };
  
  const handleViewDatasets = () => {
    router.push('/dashboard/datasets');
  };
  
  return (
    <Container size="md" py="xl">
      
      <ManageMappingModal
        opened={modalOpen}
        onClose={() => {
          setMappingModalOpen(false);
          loadProfiles();
        }}
      />

      <Card withBorder shadow="sm" p="lg" radius="md">
        <LoadingOverlay visible={loading} />
        
        <Title order={2} mb="md">Upload New Dataset</Title>
        
        <Stepper active={active} onStepClick={setActive} allowNextStepsSelect={false}>
          <Stepper.Step
            label="Dataset Information"
            description="Provide dataset details"
            icon={<IconFile style={{ width: rem(18), height: rem(18) }} />}
          >
            <TextInput
              label="Dataset Name"
              placeholder="Enter a name for this dataset"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              error={nameError}
              mb="md"
            />
            
            <Textarea
              label="Description"
              placeholder="Enter a description for this dataset"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              mb="md"
              minRows={3}
            />
            
            <FileInput
              label="Upload File"
              placeholder="Select CSV or Excel file"
              accept=".csv,.xls,.xlsx"
              required
              value={file}
              onChange={setFile}
              error={fileError}
              mb="md"
              leftSection={<IconUpload size="1rem" />}
              description="Upload a CSV or Excel file containing loan data"
            />

            <Checkbox
                onChange={(e)=>setMappingUse(e.currentTarget.checked)}
                label="Use mappings for upload"
                mb="md"
            />
            <Group>
              <Select
                  label="Select mapping to be used"
                  placeholder="Pick one"
                  mb="md"
                  disabled = {!useMappings}
                  //Mod hvb @ 17/11/2025 for soft-coded mappings
                  /*data={[
                    { value: 'mapping1', label: 'mappings1' },
                    { value: 'mapping2', label: 'mappings2' }
                  ]}*/
                  data = {mappingSelectData}
                  onChange = {(v)=>setMappingName(v??"")}
              />
              <Button onClick={() => setMappingModalOpen(true)}>Manage Mapping</Button>
            </Group>
            
            <Group justify="flex-end" mt="xl">
              <Button variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button onClick={handleSubmit}>
                Next
              </Button>
            </Group>
          </Stepper.Step>
          
          <Stepper.Step
            label="Confirmation"
            description="Confirm upload"
            icon={<IconCheck style={{ width: rem(18), height: rem(18) }} />}
          >
            <Text fw={500} mb="xs">Please confirm the following details:</Text>
            
            <Text>
              <strong>Dataset Name:</strong> {name}
            </Text>
            
            <Text>
              <strong>Description:</strong> {description || 'No description provided'}
            </Text>
            
            <Text>
              <strong>File:</strong> {file?.name} ({file?.size ? (file.size / 1024 / 1024).toFixed(2) + ' MB' : 'Unknown size'})
            </Text>
            
            {error && (
              <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" mt="md">
                {error}
              </Alert>
            )}
            
            <Group justify="flex-end" mt="xl">
              <Button variant="outline" onClick={() => setActive(0)}>
                Back
              </Button>
              <Button onClick={handleUpload}>
                Upload Dataset
              </Button>
            </Group>
          </Stepper.Step>
          
          <Stepper.Step
            label="Uploading"
            description="Processing data"
            icon={<IconUpload style={{ width: rem(18), height: rem(18) }} />}
          >
            <Text mb="md">Uploading and processing your dataset...</Text>
            
            <Progress
              value={uploadProgress}
              size="xl"
              radius="xl"
              mb="md"
              striped
              animated
            />
            <Text ta="center" mb="md">{Math.round(uploadProgress)}%</Text>
            
            <Text size="sm" c="dimmed">
              This may take a few minutes depending on the file size.
            </Text>
          </Stepper.Step>
          
          <Stepper.Completed>
            <Alert icon={<IconCheck size="1rem" />} title="Success" color="green">
              Your dataset has been uploaded successfully! You will be redirected to the datasets page.
            </Alert>
            
            <Group justify="center" mt="xl">
              <Button onClick={handleViewDatasets}>
                View All Datasets
              </Button>
            </Group>
          </Stepper.Completed>
        </Stepper>
      </Card>
    </Container>
  );
}
