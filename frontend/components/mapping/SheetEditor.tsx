// app/mapping/components/SheetEditor.tsx
"use client";
import React from "react";
import { Button, Card, Group, NumberInput, TextInput,Text,Select } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { SheetConfig } from "@/src/types/mappings";
import { FormValues } from "@/src/types/mapping-form";

type Props = {
  form: UseFormReturnType<FormValues>;
};

export function SheetEditor({ form }: Props){
  const sheets = form.values.sheets;

  function addSheet(): void {
    form.insertListItem("sheets", {
      sheet_index: sheets.length ? sheets[sheets.length - 1].sheet_index + 1 : 0,
      //alias: "",
      sheet_alias:"",
      header_row: -1,
      skip_rows: 0,
      cols_to_read: "",
      key_columns: [],
      extra: [],
      cleanup: []
    } as SheetConfig);
  }

  function removeSheet(index: number): void {
    form.removeListItem("sheets", index);
  }

  return (
    <div>
      {sheets.map((_, idx) => (
        <Card shadow="sm" p="md" mt="sm" key={idx}>
          <Group grow>
            <NumberInput label="Sheet Index" {...form.getInputProps(`sheets.${idx}.sheet_index`)} />
            {/* <TextInput label="Alias" {...form.getInputProps(`sheets.${idx}.alias`)} /> */}
            <TextInput label="Alias" {...form.getInputProps(`sheets.${idx}.sheet_alias`)} />
          </Group>

          <Group grow mt="sm">
            <NumberInput label="Header Row" {...form.getInputProps(`sheets.${idx}.header_row`)} />
            <NumberInput label="Skip Rows" {...form.getInputProps(`sheets.${idx}.skip_rows`)} />
          </Group>

          <TextInput mt="sm" label="Cols to Read (CSV)" {...form.getInputProps(`sheets.${idx}.cols_to_read`)} />

          <TextInput mt="sm" label="Key Columns (CSV or JSON)" {...form.getInputProps(`sheets.${idx}.key_columns`)} />

          {/* extras editor */}
          <div style={{ marginTop: 12 }}>
            <Group justify="space-between" mb="xs">
              <Text fw={600}>Extra Columns</Text>
              <Button size="xs" onClick={() =>
                form.insertListItem(`sheets.${idx}.extra`, { source_col: "", target_name: "" })
              }>
                Add Extra
              </Button>
            </Group>

            {(form.values.sheets[idx].extra ?? []).map((_: any, eidx: number) => (
              <Group key={eidx} grow gap="sm" mt="xs" align="flex-end">
                <TextInput
                  label="Source (col index or name)"
                  {...form.getInputProps(`sheets.${idx}.extra.${eidx}.source_col`)}
                />
                <TextInput
                  label="Target name"
                  {...form.getInputProps(`sheets.${idx}.extra.${eidx}.target_name`)}
                />
                <Button
                  size="xs"
                  c="red"
                  onClick={() => form.removeListItem(`sheets.${idx}.extra`, eidx)}
                >
                  Remove
                </Button>
              </Group>
            ))}
          </div>

          {/* CLEANUP editor */}
          <div style={{ marginTop: 12 }}>
            <Group justify="space-between" mb="xs">
              <Text fw={600}>Cleanup Rules</Text>

              <Button
                size="xs"
                onClick={() =>
                  form.insertListItem(`sheets.${idx}.cleanup`, {
                    col: 0,
                    type: "str",
                  })
                }
              >
                Add Cleanup
              </Button>
            </Group>

            {(form.values.sheets[idx].cleanup ?? []).map((rule, cidx) => (
              <Group key={cidx} gap="sm" grow mt="xs" align="flex-end">
                <NumberInput
                  label="Column Index"
                  {...form.getInputProps(`sheets.${idx}.cleanup.${cidx}.col`)}
                  min={0}
                />

                <Select
                  label="Type"
                  data={[
                    { value: "dt", label: "Date" },
                    { value: "int", label: "Integer" },
                    { value: "float", label: "Float" },
                    { value: "str", label: "String" }
                  ]}
                  {...form.getInputProps(`sheets.${idx}.cleanup.${cidx}.type`)}
                />

                <Button
                  size="xs"
                  c="red"
                  onClick={() =>
                    form.removeListItem(`sheets.${idx}.cleanup`, cidx)
                  }
                >
                  Remove
                </Button>
              </Group>
            ))}
          </div>


          <Button mt="sm" color="red" onClick={() => removeSheet(idx)}>Remove Sheet</Button>
        </Card>
      ))}

      <Button mt="md" onClick={addSheet}>Add Sheet</Button>
    </div>
  );
}
