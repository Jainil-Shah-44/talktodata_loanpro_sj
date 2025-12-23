import { useEffect, useState } from "react";
import { ActionIcon, Button, Card, Group, NumberInput, Select, Stack, TextInput } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { FormValues } from "@/src/types/mapping-form";
import { IconPlus, IconTrash } from "@tabler/icons-react";
import { mappingService } from "@/src/api/mappingService";
import { ColumnInfo } from "@/src/types/mappings";

export function ColumnsStep({ form }: { form: UseFormReturnType<FormValues> }) {
  const mappings = form.values.column_mappings;

  // ======================================
  // 1) Fetch target columns from API
  // ======================================
  const [allTargets, setAllTargets] = useState<ColumnInfo[]>([]);

  useEffect(() => {
    (async () => {
      const res = await mappingService.getFields();
      setAllTargets(res);
    })();
  }, []);

  // ======================================
  // 2) Filter out already chosen target columns
  // ======================================
  const usedTargets = mappings.map((m) => m.target_column).filter(Boolean);

  const availableTargets = allTargets
  .filter((col) => !usedTargets.includes(col.column_name))
  .map((col) => col.column_name);

  /*const add = () =>
    form.insertListItem("column_mappings", { sheet_index: 0, source_col: "", target_column: "" });*/
   // ======================================
  // 3) Add/remove mapping functions
  // ======================================
  const add = () =>
    form.insertListItem("column_mappings", {
      sheet_index: 0,
      source_col: "",
      target_column: ""
    });

    const remove = (i: number) => form.removeListItem("column_mappings", i);

  return (
    <Stack>
      {mappings.map((_, i) => {
        // Dropdown options must include the existing value (otherwise dropdown loses the value)
        const options = [
          ...(form.values.column_mappings[i].target_column
            ? [form.values.column_mappings[i].target_column]
            : []),
          ...availableTargets
        ]
          .filter((v, idx, arr) => arr.indexOf(v) === idx) // remove duplicates
          .map((v) => ({ value: v, label: v }));

        return (
          <Card key={i} p="md">
            <Group gap="md" grow align="flex-end">
              <NumberInput
                label="Sheet Index"
                {...form.getInputProps(`column_mappings.${i}.sheet_index`)}
              />

              <TextInput
                label="Source Column"
                {...form.getInputProps(`column_mappings.${i}.source_col`)}
              />

              <Select
                label="Target Column"
                placeholder="Select DB column"
                data={options}
                {...form.getInputProps(`column_mappings.${i}.target_column`)}
                searchable
                clearable={false}
              />

              {/* Remove button (small red icon) */}
              <ActionIcon
                variant="light"
                color="red"
                size="lg"
                onClick={() => remove(i)}
              >
                <IconTrash size={18} />
              </ActionIcon>
            </Group>
          </Card>
        );
      })}

      {/* Add button (green icon) */}
      <ActionIcon
        variant="light"
        color="green"
        size="xl"
        onClick={add}
        style={{ alignSelf: "flex-start", marginTop: 12 }}
      >
        <IconPlus size={22} />
      </ActionIcon>
    </Stack>
  );
}
