"use client";
import { ActionIcon, Group, Text, Transition } from "@mantine/core";
import { useState } from "react";
import { IconUpload, IconPencil, IconTrash, icons, IconRotateRectangle } from "@tabler/icons-react";

type ActionButtonsProps = {
  onAction?: (action: "load" | "rename" | "delete" | "update") => void;
};

export function FitlerSaveActions({ onAction }: ActionButtonsProps) {
  const [hovered, setHovered] = useState<string | null>(null);

  const buttons = [
    {
      key: "load",
      icon: <IconUpload size={18} />,
      label: "Load",
      color: "green",
    },
    {
      key: "rename",
      icon: <IconPencil size={18} />,
      label: "Rename",
      color: "blue",
    },
    {
      key: "delete",
      icon: <IconTrash size={18} />,
      label: "Delete",
      color: "red",
    },
    {
      key: "update",
      icon: <IconRotateRectangle size={18} />,
      label: "Update",
      color: "orange",
    }
  ] as const;

  return (
    <Group gap="md" align="center" mt={25}>
      {buttons.map((btn) => (
        <Group
          key={btn.key}
          gap={4}
          align="center"
          onMouseEnter={() => setHovered(btn.key)}
          onMouseLeave={() => setHovered(null)}
          style={{
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
        >
          <ActionIcon color={btn.color} variant="light" radius="xl" size="lg" onClick={() => onAction?.(btn.key)}>
            {btn.icon}
          </ActionIcon>

          <Transition
            mounted={hovered === btn.key}
            transition="slide-right"
            duration={150}
            timingFunction="ease"
          >
            {(styles) => (
              <Text style={styles} fw={500} c={btn.color} onClick={() => onAction?.(btn.key)}>
                {btn.label}
              </Text>
            )}
          </Transition>
        </Group>
      ))}
    </Group>
  );
}
