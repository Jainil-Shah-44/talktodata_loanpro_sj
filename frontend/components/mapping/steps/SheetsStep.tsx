import { Button, Card, Group, NumberInput, TextInput, Text, Stack } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { FormValues } from "@/src/types/mapping-form";
import ExtraEditor from "./parts/ExtraEditor";
import CleanupEditor from "./parts/CleanupEditor";
import { useState } from "react";

interface SheetStepProps{
  setStepValid:(isValid:boolean)=>void,
  form: UseFormReturnType<FormValues>
}

//export function SheetsStep({ form }: { form: UseFormReturnType<FormValues> }) {
export function SheetsStep({ form,setStepValid }: SheetStepProps) {
  const sheets = form.values.sheets;
  const [duplicateMessage,setDuplicateMessage] = useState("");

  const add = () => {
    form.insertListItem("sheets", {
      sheet_index: sheets.length + 1,
      //alias: "",
      sheet_alias: "",
      header_row: -1,
      skip_rows: 0,
      cols_to_read: "",
      key_columns: [],
      extra: [],
      cleanup: []
    });
  };

  const remove = (i: number) => form.removeListItem("sheets", i);
  
  const hasDuplicates = (arr:string[]) => {
    return new Set(arr).size !== arr.length;
  };

  return (
    <Stack>
      {sheets.map((_, idx) => (
        <Card key={idx} shadow="sm" p="md">
          <Group gap="md" grow>
            <NumberInput label="Sheet Index (Start from 1)" {...form.getInputProps(`sheets.${idx}.sheet_index`)} />
            <TextInput label="Alias" {...form.getInputProps(`sheets.${idx}.sheet_alias`)} />
          </Group>

          <Group gap="md" grow mt="sm">
            <NumberInput label="Header Row" {...form.getInputProps(`sheets.${idx}.header_row`)} />
            <NumberInput label="Skip Rows" {...form.getInputProps(`sheets.${idx}.skip_rows`)} />
          </Group>

          <TextInput mt="sm" label="Columns to Read (CSV)" {...form.getInputProps(`sheets.${idx}.cols_to_read`)} onChange={(e)=>
            {
              if(hasDuplicates(e.currentTarget.value.split(",")))
              {
                  setStepValid(false);
                  setDuplicateMessage("Duplicates not allowed.");
              }
              else
              {
                setStepValid(true);
                setDuplicateMessage("");
              }
              
              form.setFieldValue(
                  `sheets.${idx}.cols_to_read`,e.currentTarget.value);
            }
          } />
          <Text c="red">{duplicateMessage}</Text>
          <TextInput   label="Key Columns (CSV)" {...form.getInputProps(`sheets.${idx}.key_columns`)}
                  onChange={(e) =>
                  form.setFieldValue(
                  `sheets.${idx}.key_columns`,
                e.currentTarget.value.split(",").map((v) => v.trim())
              )
              }
          />
          
          <ExtraEditor form={form} idx={idx} />
          <CleanupEditor form={form} idx={idx} />

          <Button color="red" mt="sm" onClick={() => remove(idx)}>
            Remove Sheet
          </Button>
        </Card>
      ))}

      <Button onClick={add}>Add Sheet</Button>
    </Stack>
  );
}
