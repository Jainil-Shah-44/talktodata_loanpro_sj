import { Text, Stack, Code, Alert } from "@mantine/core";
import { UseFormReturnType } from "@mantine/form";
import { FormValues } from "@/src/types/mapping-form";
import { IconExclamationCircleFilled } from "@tabler/icons-react";

interface ReviewStepProps{
  form : UseFormReturnType<FormValues>,
  errorMessage : string
};

//export function ReviewStep({ form }: { form: UseFormReturnType<FormValues> }) {
export function ReviewStep({ form,errorMessage }: ReviewStepProps) {
  const preview = {
    ...form.values,
    sheets: form.values.sheets.map((s) => ({
      ...s,
      extra: s.extra && s.extra.length > 0 ? s.extra : null,
      cleanup: s.cleanup && s.cleanup.length > 0 ? s.cleanup : null
    }))
  };

  return (
    <Stack>
      <Text fw={600}>Review Your Mapping Profile</Text>

      <Code block>
        {JSON.stringify(preview, null, 2)}
      </Code>

      <Text c="dimmed" fz="sm">Press “Save” to finalize.</Text>
      {
        errorMessage && errorMessage != "" ? 
        <Alert variant="light" color="red" title="Save failed" mt="5" icon={<IconExclamationCircleFilled/>}>
            {errorMessage}
         </Alert>
      : <></>
      }
    </Stack>
  );
}
