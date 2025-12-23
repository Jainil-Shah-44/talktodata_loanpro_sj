"use client";

import { Modal } from "@mantine/core";
import { FullProfileResponse } from "@/src/types/mappings";
import {MappingWizard} from "./MappingWizard";

type Props = {
  opened: boolean;
  onClose: () => void;
  profile?: FullProfileResponse | null;
};

//export function ManageMappingModal({ opened, onClose, profile }: Props) {
export function ManageMappingModalWizBased({ opened, onClose, profile }: Props) {
  return (
    <Modal 
      opened={opened} 
      onClose={onClose} 
      title={profile ? "Edit Mapping Profile" : "Create Mapping Profile"}
      size="xl" 
      centered
    >
      <MappingWizard profile={profile} onClose={onClose} />
    </Modal>
  );
}
