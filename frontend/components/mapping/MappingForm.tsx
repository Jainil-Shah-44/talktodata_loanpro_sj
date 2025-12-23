// app/mapping/components/MappingForm.tsx
"use client";
import React, { useEffect } from "react";
import { Button, Group, TextInput, Textarea, Divider, ScrollArea } from "@mantine/core";
import { useForm } from "@mantine/form";
import {
  FullProfileResponse,
  SheetConfig,
  ColumnMapping,
  Relation
} from "@/src/types/mappings";
import { FormValues } from "@/src/types/mapping-form";
import {SheetEditor} from "./SheetEditor";
import {ColumnMappingEditor} from "./ColumnMappingEditor";
import {RelationEditor} from "./RelationEditor";
import { mappingService } from "@/src/api/mappingService";

type Props = {
  profile: FullProfileResponse | null;
  onSaved: () => void;
  onCancel: () => void;
};

export default function MappingForm({ profile, onSaved, onCancel }: Props) {
  const form = useForm<FormValues>({
    initialValues: {
      name: profile?.name ?? '',
      description: profile?.description ?? '',
      is_global: true,
      sheets: profile?.sheets.map((s) => ({
        ...s,
        alias: s.sheet_alias ?? ""  
        }))??[{
        sheet_index: 0,
        alias: "",      // <--- REQUIRED
        header_row: -1,
        skip_rows: 0,
        cols_to_read: "",
        key_columns: [],
        extra: [],
        cleanup: []
      }],
      column_mappings: [],
      relations: []
    }
  });

  useEffect(() => {
    if (profile) {
      form.setValues({
        name: profile.name,
        description: profile.description ?? null,
        is_global: profile.is_global,
        sheets: profile.sheets ?? [],
        column_mappings: profile.column_mappings ?? [],
        relations: profile.relations ?? []
      });
    } else {
      // default one sheet for UX
      form.setValues((v) => ({
        ...v,
        sheets:
          (v.sheets ?? []).length > 0
            ? v.sheets
            : [{ sheet_index: 0, header_row: -1, skip_rows: 0 }]
      }));

    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile]);

  async function handleSubmit(values: FormValues): Promise<void> {
    if (profile) {
      await mappingService.update(profile.id, values);
    } else {
      // server expects MappingProfileCreate structure; FullProfileResponse is acceptable for create
      await mappingService.create(values as unknown as FullProfileResponse);
    }
    onSaved();
  }

  return (
    <ScrollArea h="70vh">
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <TextInput label="Name" {...form.getInputProps("name")} required />
        <Textarea label="Description" {...form.getInputProps("description")} />

        <Divider my="md" label="Sheets" />
        <SheetEditor form={form} />

        <Divider my="md" label="Column Mapping" />
        <ColumnMappingEditor form={form} />

        <Divider my="md" label="Relations" />
        <RelationEditor form={form} />

        <Group justify="flex-end" mt="lg">
          <Button variant="outline" onClick={onCancel}>Cancel</Button>
          <Button type="submit">Save</Button>
        </Group>
      </form>
    </ScrollArea>
  );
}
