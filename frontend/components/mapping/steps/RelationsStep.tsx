import { Button, Card, Group, NumberInput, TextInput, Stack } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { FormValues } from "@/src/types/mapping-form";

export function RelationsStep({ form }: { form: UseFormReturnType<FormValues> }) {
  const items = form.values.relations;

  const add = () =>
    form.insertListItem("relations", { left_sheet: 0, right_sheet: 0, left_col: "", right_col: "", how: "left" });

  return (
    <Stack>
      {items.map((_, i) => (
        <Card key={i} p="md">
          <Group gap="md" grow>
            <NumberInput label="Left Sheet" {...form.getInputProps(`relations.${i}.left_sheet`)} />
            <NumberInput label="Right Sheet" {...form.getInputProps(`relations.${i}.right_sheet`)} />
          </Group>

          <Group gap="md" grow mt="sm">
            <TextInput label="Left Column" {...form.getInputProps(`relations.${i}.left_col`)} />
            <TextInput label="Right Column" {...form.getInputProps(`relations.${i}.right_col`)} />
            <TextInput label="Join Type" {...form.getInputProps(`relations.${i}.how`)} />
          </Group>

          <Button color="red" mt="sm" onClick={() => form.removeListItem("relations", i)}>
            Remove
          </Button>
        </Card>
      ))}

      <Button onClick={add}>Add Relation</Button>
    </Stack>
  );
}
