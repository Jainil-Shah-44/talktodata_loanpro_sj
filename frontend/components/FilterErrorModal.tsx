import { useState } from "react";
import { Modal, Button, Text, List, ThemeIcon } from "@mantine/core";
import { IconX } from "@tabler/icons-react";

interface FilterErrorModalProps {
  errors: string[];
  opened: boolean;
  onClose: () => void;
}

export function FilterErrorModal({ errors, opened, onClose }: FilterErrorModalProps) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="Filter Validation Errors"
      size="lg"
      centered
      overlayProps={{
            style: {
            backdropFilter: 'blur(5px)', // blur background
            backgroundColor: 'rgba(0, 0, 0, 0.5)', // semi-transparent overlay
            },
        }}
    >
      <Text mb="sm">Some filters conflict or have invalid values. Please fix them:</Text>
      <List
        spacing="sm"
        size="sm"
        center
        icon={
          <ThemeIcon color="red" size={24} radius="xl">
            <IconX size={16} />
          </ThemeIcon>
        }
      >
        {errors.map((err, index) => (
          <List.Item key={index}>{err}</List.Item>
        ))}
      </List>
      <Button mt="md" fullWidth color="red" onClick={onClose}>
        Close
      </Button>
    </Modal>
  );
}
