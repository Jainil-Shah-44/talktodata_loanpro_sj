// app/mapping/components/RelationEditor.tsx
"use client";
import React from "react";
import { Button, Card, Group, NumberInput, TextInput } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { Relation } from "@/src/types/mappings";
import { FormValues } from "@/src/types/mapping-form";

type Props = {
  form: UseFormReturnType<FormValues>;
};

export function RelationEditor({ form }: Props) {
  const relations = form.values.relations;

  function addRelation(): void {
    form.insertListItem("relations", { left_sheet: 0, right_sheet: 0, left_col: "", right_col: "", how: "left" } as Relation);
  }

  function removeRelation(idx: number): void {
    form.removeListItem("relations", idx);
  }

  return (
    <div>
      {relations.map((_, idx) => (
        <Card key={idx} p="md" mt="sm">
          <Group grow>
            <NumberInput label="Left Sheet" {...form.getInputProps(`relations.${idx}.left_sheet`)} />
            <NumberInput label="Right Sheet" {...form.getInputProps(`relations.${idx}.right_sheet`)} />
          </Group>

          <Group grow mt="sm">
            <TextInput label="Left Column" {...form.getInputProps(`relations.${idx}.left_col`)} />
            <TextInput label="Right Column" {...form.getInputProps(`relations.${idx}.right_col`)} />
            <TextInput label="How (left|inner|right)" {...form.getInputProps(`relations.${idx}.how`)} />
          </Group>

          <Button mt="sm" color="red" onClick={() => removeRelation(idx)}>Remove</Button>
        </Card>
      ))}

      <Button mt="md" onClick={addRelation}>Add Relation</Button>
    </div>
  );
}
