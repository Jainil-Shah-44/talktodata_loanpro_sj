import { TextInput, Textarea, Switch, Stack, Space,Text, FileInput } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { FormValues } from "@/src/types/mapping-form";
import { notifications } from "@mantine/notifications";
import { CreatableSelect } from "@/components/CreatableSelect";
import { useEffect, useState } from "react";
import { mappingService } from "@/src/api/mappingService";

interface ProfileStepProps{
  form: UseFormReturnType<FormValues>,
  OnJsonFileLoad:() => void
}

//export function ProfileStep({ form }: { form: UseFormReturnType<FormValues> }) {
export function ProfileStep({ form,OnJsonFileLoad }: ProfileStepProps) {

  const [fileTypesList,setFileTypeList] = useState<string[]>([]);


  useEffect(() => {
    (async () => {
      const res = await mappingService.getFileType();
      if(res!=null && res!=undefined)
        setFileTypeList(res);
    })();
  }, []);
  

  async function handleJsonUpload(file: File | null) {
  if (!file) return;

  const text = await file.text();
  try {
    const json = JSON.parse(text);

    // Validate the structure (minimal)
    if (!json.name || !json.sheets) {
      notifications.show({
        color: "red",
        message: "Invalid JSON: Missing required fields"
      });
      return;
    }

    // Auto-load JSON into form
    form.setValues({
      name: json.name ?? "",
      description: json.description ?? "",
      is_global: json.is_global ?? true,
      sheets: json.sheets ?? [],
      column_mappings: json.column_mappings ?? [],
      relations: json.relations ?? []
    });

    notifications.show({
      color: "green",
      message: "Profile loaded successfully!"
    });

    OnJsonFileLoad();


  } catch (e) {
    notifications.show({
      color: "red",
      message: "Invalid JSON format"
    });
  }
}

  return (
    <Stack gap="md">
      <TextInput label="Profile Name" {...form.getInputProps("name")} required />
      <Textarea label="Description" {...form.getInputProps("description")} autosize minRows={3} />
      <CreatableSelect
        label="FileType"
        required
        // data={["PDF", "Excel", "CSV"]}
        data={fileTypesList}
        formProps={form.getInputProps("file_type")}
      />

      <Switch
        label="Global profile"
        checked={form.values.is_global}
        onChange={(e) => form.setFieldValue("is_global", e.currentTarget.checked)}
      />
      <Space h="md"/> 
      <Text size="lg" fw="500"> OR </Text>
      <FileInput
        accept="application/json"
        label="Import Mapping Profile JSON"
        placeholder="Select JSON file"
        onChange={handleJsonUpload}
      />
    </Stack>
  );
}
