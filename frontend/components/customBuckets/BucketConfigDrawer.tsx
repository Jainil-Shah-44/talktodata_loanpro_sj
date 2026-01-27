// import { Drawer, TextInput, Button, Stack } from "@mantine/core";
// type Props = {
//   opened: boolean;
//   onClose: () => void;
//   configId: string | null;
// };

// export function BucketConfigDrawer({ opened, onClose, configId }: Props) {
//   return (
//     <Drawer opened={opened} onClose={onClose} title="Edit Summary" size="lg">
//       <Stack>
//         <TextInput label="Name" placeholder="Summary name" />
//         {/* add bucket rule editor here */}
//         <Button>Save</Button>
//       </Stack>
//     </Drawer>
//   );
// }
"use client";

import { useEffect, useState } from "react";
import {
  Drawer,
  TextInput,
  Button,
  Group,
  Switch,
  Select,
  NumberInput,
  Stack,
  Table,
  ActionIcon,
  Divider,
  Notification,
  Text,
  Modal,
} from "@mantine/core";
import { IconPlus, IconTrash } from "@tabler/icons-react";
import { bucketService } from "@/src/api/customBucketService";
import { BucketConfigListItem } from "@/src/types/custombucket";
import { showNotification } from "@mantine/notifications";
import { ColumnInfo } from "@/src/types/mappings";

// ---------------------
// Types
// ---------------------

interface NumericBucket {
  min: number | null;
  max: number | null;
  label: string;
}

interface StringBucket {
  value: string;
  label: string;
}

interface BucketConfigDrawerProps {
  datasetId: string;
  opened: boolean;
  onClose: (updated: boolean) => void;
  initialConfig?: BucketConfigListItem | null;
  //targetFields: string[];
  targetFields: ColumnInfo[];
  datasetFileType:string
}

export default function BucketConfigDrawer({
  datasetId,
  opened,
  onClose,
  initialConfig = null,
  targetFields,
  datasetFileType
}: BucketConfigDrawerProps) {
  const isEdit = !!initialConfig;

  const [name, setName] = useState("");
  const [summaryType, setSummaryType] = useState("");
  const [targetField, setTargetField] = useState<string>("");
  const [isDefault, setIsDefault] = useState(false);

  useEffect(()=>{
    if(datasetFileType!=undefined && datasetFileType != null)
      setSummaryType(datasetFileType);
  },[datasetFileType]);

  const [bucketType, setBucketType] = useState<"numeric" | "string">("numeric");
  const [numericRows, setNumericRows] = useState<NumericBucket[]>([]);
  const [stringRows, setStringRows] = useState<StringBucket[]>([]);
  const [autoStringMode, setAutoStringMode] = useState(false);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingSaveAction, setPendingSaveAction] = useState<null | (() => void)>(null);

  // --------------------------
  // Load config when editing
  // --------------------------
  useEffect(() => {
    if (initialConfig) {
      setName(initialConfig.name || "");
      setSummaryType(initialConfig.summary_type || "");
      setTargetField(initialConfig.target_field || "");
      setIsDefault(Boolean(initialConfig.is_default));

      const cfg = initialConfig.bucket_config || [];

      //if (Array.isArray(cfg) && cfg.length === 1 && cfg[0]?.all) {
      if (Array.isArray(cfg) && cfg.length === 1 && cfg[0]?.values?.[0] === "ALL") {
        setBucketType("string");
        setAutoStringMode(true);
        setStringRows([]);
      } else if (cfg.some((r) => "values" in r)) {
        setBucketType("string");
        setAutoStringMode(false);
        setStringRows(
          cfg.map((r) => ({
            value: r.values?.[0] ?? "",
            label: r.label ?? "",
          }))
        );
      } else {
        setBucketType("numeric");
        setAutoStringMode(false);
        setNumericRows(
          cfg.map((r) => ({
            min: r.min ?? null,
            max: r.max ?? null,
            label: r.label ?? "",
          }))
        );
      }
    } else {
      setName("");
      //This file type
      //setSummaryType("");
      setTargetField("");
      setIsDefault(false);
      setBucketType("numeric");
      setNumericRows([{ min: 0, max: 1000, label: "0 to 1000" }]);
      setStringRows([]);
      setAutoStringMode(false);
    }

    setError(null);
    setSaving(false);
  }, [initialConfig, opened]);

  // --------------------------
  // Numeric bucket helpers
  // --------------------------

  const addNumericRow = () =>
    setNumericRows((s) => [...s, { min: null, max: null, label: "" }]);

  const removeNumericRow = (i: number) =>
    setNumericRows((s) => s.filter((_, idx) => idx !== i));

  const updateNumericRow = (i: number, patch: Partial<NumericBucket>) =>
    setNumericRows((s) => s.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  // --------------------------
  // String bucket helpers
  // --------------------------

  const addStringRow = () =>
    setStringRows((s) => [...s, { value: "", label: "" }]);

  const removeStringRow = (i: number) =>
    setStringRows((s) => s.filter((_, idx) => idx !== i));

  const updateStringRow = (i: number, patch: Partial<StringBucket>) =>
    setStringRows((s) => s.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));

  // --------------------------
  // Build final JSON for server
  // --------------------------

  const buildBucketConfig = () => {
    if (bucketType === "numeric") {
      return numericRows.map((r) => ({
        min: r.min,
        max: r.max,
        label: r.label || "",
      }));
    }

    //"[{""all"": true}]"
    //expected
    //"[{""label"": ""All States"", ""values"": [""ALL""]}]"
    //if (autoStringMode) return [{ all: true }];
    if (autoStringMode) return [{ label : "ALL data" ,values: ["ALL"] }];

    return stringRows.map((r) => ({
      values: [r.value],
      label: r.label,
    }));
  };

  // --------------------------
  // Validation
  // --------------------------

  const validate = (): string | null => {
    if (!name.trim()) return "Name is required";
    if (!targetField) return "Target field is required";

    if (!isEdit && !summaryType.trim()) return "Summary type is required";

    if (bucketType === "numeric") {
      if (numericRows.length === 0) return "Add at least one numeric bucket";

      for (let i = 0; i < numericRows.length; i++) {
        const r = numericRows[i];
        if (r.min == null && r.max == null)
          return `Numeric bucket #${i + 1} must have min or max`;
        if (!r.label.trim())
          return `Numeric bucket #${i + 1} must have label`;
      }
    }

    if (bucketType === "string" && !autoStringMode) {
      if (stringRows.length === 0) return "Add at least one string bucket";

      for (let i = 0; i < stringRows.length; i++) {
        const r = stringRows[i];
        if (!r.value.trim())
          return `String bucket #${i + 1} must have a value`;
        if (!r.label.trim())
          return `String bucket #${i + 1} must have a label`;
      }
    }

    return null;
  };

  // --------------------------
  // Save handler
  // --------------------------

  /*const handleSave = async () => {
    const err = validate();
    if (err) {
      setError(err);
      return;
    }

    // Determine the intended dataset_id based on default toggle
    const targetDatasetId = isDefault ? null : datasetId;

    // Only check conflict if creating or changing targetDatasetId
    const isDatasetChanged =
      !initialConfig || initialConfig.dataset_id !== targetDatasetId;

    if (isDatasetChanged) {
      const exists = await bucketService.checkExists(
        isDefault ? "default" : datasetId,
        summaryType,
        targetField!
      );

      if (exists) {
        const confirmOverwrite = window.confirm(
          `A bucket config already exists for this dataset and field.\n` +
          `Do you want to overwrite it?`
        );
        if (!confirmOverwrite) return;
      }
    }

    const payload = {
      name: name.trim(),
      target_field: targetField,
      bucket_config: buildBucketConfig(),
      is_default: isDefault,
    };

    setSaving(true);
    setError(null);

    try {
      if (isEdit) {
        await bucketService.update(initialConfig!.id, payload);
      } else {
        await bucketService.create(datasetId, {
          ...payload,
          summary_type: summaryType.trim(),
          target_field:payload.target_field??""
        });
      }

      onClose(true);
    } catch {
      setError("Failed to save");
    } finally {
      setSaving(false);
    }
  };*/

  const handleSave = async () => {

    const err = validate();
    if (err) {
      setError(err);
      return;
    }

  // Determine whether scope changed
  const oldScope = initialConfig?.is_default ? "default" : "dataset";
  const newScope = isDefault ? "default" : "dataset";

  const targetDatasetId = isDefault ? null : datasetId;
  //const targetDatasetId = isDefault ? "default" : datasetId;
  const finalBucketJson = buildBucketConfig();

  setSaving(true);
  setError(null);

  // Build payload
  const is_target_json_col = targetFields.find(t=>t.column_name == targetField)?.is_json_col ?? false;

  const payload = {
    name,
    summary_type: summaryType,
    target_field: targetField,
    bucket_config: finalBucketJson,
    is_default: isDefault,
    dataset_id: targetDatasetId,
    target_field_is_json: is_target_json_col
  };

  // If scope unchanged → update normally
  if (initialConfig && oldScope === newScope) {
    //await updateConfig(initialConfig.id, payload);
    try
    {
      await bucketService.update(initialConfig!.id, payload);
      onClose(true);
      showNotification({
        title: "Bucket Updated",
        message: "Bucket configuration saved successfully.",
        color: "green"
      });
    }catch(err){
      setError("Failed to update");
    }
    finally{
      setSaving(false);
    }
    return;
  }

  // Scope changed OR creating new → We must check existence
  const exists = await bucketService.checkExists(
    isDefault ? "default" : datasetId,
    summaryType,
    targetField!
  );

  if (exists) {
    // Ask confirmation using modal
    setPendingSaveAction(() => async () => {
      // Fetch existing config ID
      try{
        const existingConfig = await bucketService.fetchByScope(
          isDefault ? "default" : datasetId,
          summaryType,
          targetField!
        );

        if (existingConfig) {
          await bucketService.update(existingConfig.id, payload);
          showNotification({
            title: "Bucket Updated",
            message: "Bucket configuration saved successfully.",
            color: "green"
          });
        } else {
          await bucketService.create(targetDatasetId??"", payload);
              showNotification({
            title: "Bucket Updated",
            message: "Bucket created successfully.",
            color: "green"
          });
        }
        onClose(true);
    }catch(err){
      setError("Failed to save");
    }
    finally{
      setSaving(false);
    }
    });

    setConfirmOpen(true);
    return;
  }

  // No conflict → create new
  try{
    await bucketService.create(targetDatasetId??"default", payload);
    showNotification({
        title: "Bucket Updated",
        message: "Bucket created successfully.",
        color: "green"
      });
    onClose(true);
  }
  catch(err){
      setError("Failed to save");
  }
  finally{
      setSaving(false);
  }
};

  // --------------------------
  // Delete handler
  // --------------------------

  const handleDelete = async () => {
    if (!isEdit) return;
    setSaving(true);

    try {
      await bucketService.remove(initialConfig!.id);
      onClose(true);
    } catch {
      setError("Failed to delete");
    } finally {
      setSaving(false);
    }
  };

  // --------------------------
  // UI Rendering
  // --------------------------

  return (
  <Drawer
    opened={opened}
    size="lg"
    title={isEdit ? "Edit Bucket Config" : "Create Bucket Config"}
    onClose={() => onClose(false)}
    padding="md"
  >
    <Stack gap="sm">
      {error && (
        <Notification color="red" onClose={() => setError(null)}>
          {error}
        </Notification>
      )}

      <TextInput
        label="Name"
        value={name}
        onChange={(e) => setName(e.currentTarget.value)}
        required
      />

      {!isEdit && (
        <TextInput
          label="File Type"
          value={summaryType}
          onChange={(e) => setSummaryType(e.currentTarget.value)}
          required
        />
      )}

      <Select
        label="Target Field"
        data={targetFields.map(c=>c.column_name)}
        value={targetField ?? null}
        onChange={(value) => setTargetField(value??"")}
        required
      />

      <Group justify="space-between">
        <Switch
          label="Is Default"
          checked={isDefault}
          onChange={(e) => setIsDefault(e.currentTarget.checked)}
        />

        <Select
          label="Bucket Type"
          value={bucketType}
          onChange={(v: any) => setBucketType(v)}
          data={[
            { value: "numeric", label: "Numeric" },
            { value: "string", label: "String" },
          ]}
          w={200}
        />
      </Group>

      <Divider />

      {/* NUMERIC BUCKETS */}
      {bucketType === "numeric" && (
        <>
          <Group justify="space-between">
            <Text fw={500}>Numeric Buckets</Text>

            <Button size="xs" leftSection={<IconPlus size={14} />} onClick={addNumericRow}>
              Add
            </Button>
          </Group>

          <Table>
            <thead>
              <tr>
                <th>Min</th>
                <th>Max</th>
                <th>Label</th>
                <th />
              </tr>
            </thead>

            <tbody>
              {numericRows.map((r, i) => (
                <tr key={i}>
                  <td>
                    <NumberInput
                      value={r.min ?? undefined}
                      onChange={(value) =>
                        updateNumericRow(i, {
                          min: typeof value === "number" ? value : null,
                        })
                      }
                      hideControls
                    />
                  </td>

                  <td>
                    <NumberInput
                      value={r.max ?? undefined}
                      onChange={(value) =>
                        updateNumericRow(i, {
                          max: typeof value === "number" ? value : null,
                        })
                      }

                      hideControls
                    />
                  </td>

                  <td>
                    <TextInput
                      value={r.label}
                      onChange={(e) => updateNumericRow(i, { label: e.currentTarget.value })}
                    />
                  </td>

                  <td>
                    <ActionIcon color="red" onClick={() => removeNumericRow(i)}>
                      <IconTrash size={16} />
                    </ActionIcon>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}

      {/* STRING BUCKETS */}
      {bucketType === "string" && (
        <>
          <Group justify="space-between">
            <Text fw={500}>String Buckets</Text>

            <Button
              size="xs"
              leftSection={<IconPlus size={14} />}
              onClick={addStringRow}
              disabled={autoStringMode}
            >
              Add
            </Button>
          </Group>

          <Switch
            label="Auto-group ALL unique values"
            checked={autoStringMode}
            onChange={(e) => setAutoStringMode(e.currentTarget.checked)}
          />

          {!autoStringMode && (
            <Table>
              <thead>
                <tr>
                  <th>Value</th>
                  <th>Label</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {stringRows.map((r, i) => (
                  <tr key={i}>
                    <td>
                      <TextInput
                        value={r.value}
                        onChange={(e) => updateStringRow(i, { value: e.currentTarget.value })}
                      />
                    </td>

                    <td>
                      <TextInput
                        value={r.label}
                        onChange={(e) => updateStringRow(i, { label: e.currentTarget.value })}
                      />
                    </td>

                    <td>
                      <ActionIcon color="red" onClick={() => removeStringRow(i)}>
                        <IconTrash size={16} />
                      </ActionIcon>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </>
      )}

      <Divider />

      <Group justify="space-between">
        {isEdit ? (
          <Button color="red" onClick={handleDelete} loading={saving}>
            Delete
          </Button>
        ) : (
          <div />
        )}

        <Group>
          <Button variant="default" onClick={() => onClose(false)}>
            Cancel
          </Button>

          <Button onClick={handleSave} loading={saving}>
            {isEdit ? "Save Changes" : "Create"}
          </Button>
        </Group>
      </Group>
    </Stack>
    <Modal
      opened={confirmOpen}
      onClose={() => setConfirmOpen(false)}
      title="Overwrite Existing Bucket?">
        <Text mb="md">
          A bucket configuration already exists for this scope.  
          Do you want to overwrite it?
        </Text>

        <Group justify="flex-end" gap="md">
          <Button variant="outline" onClick={() => setConfirmOpen(false)}>
            Cancel
          </Button>
          <Button
            color="red"
            onClick={() => {
              setConfirmOpen(false);
              pendingSaveAction?.(); // execute actual save
            }}>
            Overwrite
          </Button>
        </Group>
    </Modal>
  </Drawer>
);
}
