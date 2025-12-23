import { NavLink, ScrollArea, Button, Stack, Loader } from "@mantine/core";
import { IconPlus } from "@tabler/icons-react";
import { useBucketConfigs } from "@/hooks/useBucketConfigs";

type Props = {
  datasetId: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onEdit: (id: string) => void;
};

export function BucketSidebar({
  datasetId,
  selectedId,
  onSelect,
  onCreate,
  onEdit,
}: Props) {
  const { data, isLoading } = useBucketConfigs(datasetId);

  return (
    <div style={{ width: 280, borderRight: "1px solid #eee" }}>
      <Stack p="sm">
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={onCreate}
          variant="light"
        >
          New Summary
        </Button>
      </Stack>

      <ScrollArea h="calc(100vh - 60px)">
        {isLoading && <Loader m="md" />}

        {data?.map((cfg) => (
          <NavLink
            key={cfg.id}
            label={cfg.name}
            active={selectedId === cfg.id}
            onClick={() => onSelect(cfg.id)}
            rightSection={
              <Button
                size="xs"
                variant="subtle"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(cfg.id);
                }}
              >
                Edit
              </Button>
            }
          />
        ))}
      </ScrollArea>
    </div>
  );
}
