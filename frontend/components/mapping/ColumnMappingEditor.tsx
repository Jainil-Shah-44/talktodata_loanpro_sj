// app/mapping/components/ColumnMappingEditor.tsx
"use client";
import React from "react";
import { Button, Card, Group, NumberInput, TextInput } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { ColumnMapping } from "@/src/types/mappings";
import { FormValues } from "@/src/types/mapping-form";

type Props = {
  form: UseFormReturnType<FormValues>;
};

export function ColumnMappingEditor({ form }: Props) {
  const mappings = form.values.column_mappings;

  function addMapping(): void {
    form.insertListItem("column_mappings", {
      sheet_index: 0,
      source_col: "",
      target_column: ""
    } as ColumnMapping);
  }

  function removeMapping(idx: number): void {
    form.removeListItem("column_mappings", idx);
  }

  return (
    <div>
      {mappings.map((_, idx) => (
        <Card key={idx} p="md" mt="sm">
          <Group grow>
            <NumberInput label="Sheet Index" {...form.getInputProps(`column_mappings.${idx}.sheet_index`)} />
            <TextInput label="Source Column" {...form.getInputProps(`column_mappings.${idx}.source_col`)} />
            <TextInput label="Target Column" {...form.getInputProps(`column_mappings.${idx}.target_column`)} />
          </Group>

          <Button mt="sm" color="red" onClick={() => removeMapping(idx)}>Remove</Button>
        </Card>
      ))}

      <Button mt="md" onClick={addMapping}>Add Mapping</Button>
    </div>
  );
}
