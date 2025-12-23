// app/mapping/components/ManageMappingModal.tsx
"use client";
import React, { useEffect, useState } from "react";
import { Modal, Button, Table, Group, Text, Checkbox, Paper, ActionIcon } from "@mantine/core";
import { MappingProfileSummary, FullProfileResponse } from "@/src/types/mappings";
import { mappingService } from "@/src/api/mappingService";
//import MappingForm from "./MappingForm";
import { ManageMappingModalWizBased } from "./ManageMappingModalWizBased";
import { useUserStore } from '@/src/store/userStore';
import { IconPencil, IconTrash } from "@tabler/icons-react";
// import { modals } from "@mantine/modals";

type Props = {
  opened: boolean;
  onClose: () => void;
};

export function ManageMappingModal({ opened, onClose }: Props) {
   const [profiles, setProfiles] = useState<MappingProfileSummary[]>([]);
  const [editingProfile, setEditingProfile] = useState<FullProfileResponse | null>(null);
  const [showForm, setShowForm] = useState(false);
  const loggedInUser = useUserStore().user;
  
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [targetId, setTargetId] = useState<number | null>(null);
  const [permanentDelete,setPermanentDelete] = useState(false);

  useEffect(() => {
    if (opened) load();
  }, [opened]);

  async function load(): Promise<void> {
    const items = await mappingService.list();
    setProfiles(items);
  }

  async function handleEdit(id: number): Promise<void> {
    const full = await mappingService.getById(id);
    setEditingProfile(full);
    setShowForm(true);
  }

  async function handleCreate(): Promise<void> {
    setEditingProfile(null);
    setShowForm(true);
  }

  function PermanentDeleteContent({
  permanentDelete,
  setPermanentDelete,
  }: {
    permanentDelete: boolean;
    setPermanentDelete: (v: boolean) => void;
  }) {
    return (
      <div>
        <div>Are you sure you want to delete this mapping profile?</div>

        <Checkbox
          mt="md"
          label="Delete permanently (cannot be undone)"
          checked={permanentDelete}
          onChange={(e) => setPermanentDelete(e.currentTarget.checked)}
        />
      </div>
    );
  }

  // async function handleDelete(id: number): Promise<void> {
  //   /*if (confirm("Delete mapping profile?")) {
  //     await mappingService.remove(id);
  //     await load();
  //   }*/
  //   modals.openConfirmModal({
  //     title: "Delete Mapping Profile",
  //     centered: true,

  //     children: loggedInUser?.is_su ? (
  //       <PermanentDeleteContent
  //         permanentDelete={permanentDelete}
  //         setPermanentDelete={setPermanentDelete}
  //       />
  //     ) : (
  //       "Are you sure you want to delete this mapping profile?"
  //     ),

  //     labels: { confirm: "Delete", cancel: "Cancel" },
  //     confirmProps: { color: "red" },

  //     onConfirm: async () => {
  //       if(permanentDelete)
  //       {
  //         await mappingService.removePermenant(id);
  //       }else{
  //         await mappingService.remove(id);
  //       }
  //       await load();
  //     },
  //   });
  // }

  return (
    <Modal opened={opened} onClose={onClose} title="Manage Mapping Profiles" size="80%">
      <Modal
        opened={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Mapping Profile"
        centered
      >
        <div>Are you sure you want to delete this mapping profile?</div>

        {loggedInUser?.is_su && (
          <Checkbox
            mt="md"
            label="Delete permanently (cannot be undone)"
            checked={permanentDelete}
            onChange={(e) => setPermanentDelete(e.currentTarget.checked)}
          />
        )}

        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={() => setDeleteModalOpen(false)}>
            Cancel
          </Button>

          <Button
            color="red"
            onClick={async () => {
              if (targetId) {
                if(permanentDelete)
                    await mappingService.removePermenant(targetId);
                else
                     await mappingService.remove(targetId);
                await load();
              }
              setDeleteModalOpen(false);
            }}
          >
            Delete
          </Button>
        </Group>
      </Modal>
      {!showForm ? (
        <>
          <Group justify="space-between" mb="md">
            <Text fw={700}>Profiles</Text>
            <Button onClick={handleCreate} color="teal">Create</Button>
          </Group>

          {/* <Table striped highlightOnHover> */}
          <Paper withBorder radius="md" p="sm">
            <Table striped highlightOnHover
              withTableBorder withColumnBorders={false} verticalSpacing="sm" 
              horizontalSpacing="lg" stickyHeader stickyHeaderOffset={60}>
              <thead>
                <tr>
                  <th style={{ padding:5,fontWeight: 600, background: "#f8f9fa" }}>Name</th>
                  <th style={{ padding:5,fontWeight: 600, background: "#f8f9fa" }}>Description</th>
                  <th style={{ padding:5,fontWeight: 600, background: "#f8f9fa" }}>Global</th>
                  <th style={{ padding:5,fontWeight: 600, background: "#f8f9fa" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {profiles.map((p) => (
                  <tr key={p.id}>
                    <td style={{ padding: "12px 16px" }}>{p.name}</td>
                    <td>{p.description ?? "-"}</td>
                    <td>{p.is_global ? "Yes" : "No"}</td>
                    <td>
                      <Group gap="xs">
                        <ActionIcon variant="light" color="blue" onClick={() => handleEdit(p.id)}>
                          <IconPencil size={16} />
                        </ActionIcon>

                        <ActionIcon variant="light" color="red" onClick={() => {
                            setTargetId(p.id);
                            setPermanentDelete(false);
                            setDeleteModalOpen(true);
                          }}>
                          <IconTrash size={16} />
                        </ActionIcon>
                      </Group>
                      {/* <Group gap="sm" justify="center">
                        <Button size="xs" onClick={() => handleEdit(p.id)}>Edit</Button>
                        <Button size="xs" color="red" onClick={() => {
                            setTargetId(p.id);
                            setPermanentDelete(false);
                            setDeleteModalOpen(true);
                          }}>Delete</Button>
                      </Group> */}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Paper>
        </>
      ) : (
        <ManageMappingModalWizBased
          opened={showForm}
          profile={editingProfile}
          onClose={async () => {
            setShowForm(false);
            await load();
          }}
        />
      )}
    </Modal>
  );
}