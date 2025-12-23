import { Table, Loader, Center, Switch, Group } from "@mantine/core";
import { useBucketSummaries } from "@/hooks/useBucketSummaries";
import { BucketSummaryRequest } from "@/src/types/custombucket";
import { Button } from "@mantine/core";
import { IconDownload } from "@tabler/icons-react";
import { exportBucketSummaryToExcel } from "@/src/utils/exportToExcel";
import { formatCrores } from "@/src/utils/numberFormat";
type Props = {
  datasetId: string;
  configId: string | null;
  filters: any;
  showEmpty: boolean;
  onToggleEmpty: () => void;
  useFilters:boolean,
  onToggleUseFilters: ()=> void;
};

// Format number with commas and optional decimal places
const formatNumber = (num: number, decimals = 2) => {
  if (num === null || num === undefined) return '-';
  return num.toLocaleString('en-IN', { 
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

// Format currency in lakhs/crores for Indian format
// const formatCurrency = (num: number) => {
//   if (num === null || num === undefined) return '-';
//   if (num === 0) return '0.00';
  
//   // Convert to appropriate scale based on value
//   if (num >= 10000000) { // 1 crore = 10,000,000
//     return `${(num / 10000000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Cr`;
//   } else if (num >= 100000) { // 1 lakh = 100,000
//     return `${(num / 100000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} L`;
//   } else if (num >= 1000) { // For thousands
//     return `${(num / 1000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}K`;
//   } else {
//     return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
//   }
// };


// Format percentage
const formatPercent = (value: any) => {
  const num = Number(value);
  if (isNaN(num)) return '-';
  return `${num.toFixed(2)}%`;
};

export function BucketSummaryTable({
  datasetId,
  configId,
  filters,
  showEmpty,
  onToggleEmpty,
  useFilters,
  onToggleUseFilters,
}: Props) {
  const payload: BucketSummaryRequest | null = configId
    ? {
        config_ids: [configId],
        //Mod hvb @ 08/12/2025 for passing empty array
        //filters: useFilters == true ? filters : {},
        filters: useFilters == true ? filters : null,
        show_empty_buckets: showEmpty,
      }
    : null;

  const { data, isLoading } = useBucketSummaries(datasetId, payload,useFilters);

  if (isLoading)
    return (
      <Center>
        <Loader m="xl" />
      </Center>
    );

  if (!data || data.length === 0)
    return (
      <Center m="xl" c="dimmed">
        No summary found
      </Center>
    );

  const summary = data[0];

//added by jainil - export to excel button
  return (
    <div style={{ padding: 20 }}>
      {/* <Group>
        <Switch
          checked={showEmpty}
          onChange={onToggleEmpty}
          label="Show empty buckets"
          mb="md"
        />

        <Switch
          checked={useFilters}
          onChange={onToggleUseFilters}
          label="Use filters in sumamry"
          mb="md"
        />
      </Group> */}

    <Group justify="space-between">
        <Group>
          <Switch
            checked={showEmpty}
            onChange={onToggleEmpty}
            label="Show empty buckets"
            mb="md"
          />

          <Switch
            checked={useFilters}
            onChange={onToggleUseFilters}
            label="Use filters in summary"
            mb="md"
          />
        </Group>

      <Button
        size="xs"
        variant="outline"
        leftSection={<IconDownload size={14} />}
        onClick={() =>
          exportBucketSummaryToExcel(
            summary.buckets,
            `Bucket_Summary_${configId ?? "all"}`
          )
        }
      >
        Export to Excel
      </Button>
    </Group>

      <Table striped highlightOnHover withTableBorder withColumnBorders stickyHeader> 
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Bucket</Table.Th>
            <Table.Th>Count</Table.Th>
            <Table.Th>POS</Table.Th>
            <Table.Th>POS %</Table.Th>
            <Table.Th>Post NPA</Table.Th>
            <Table.Th>Post W/OFF</Table.Th>
            <Table.Th>6M</Table.Th>
            <Table.Th>12M</Table.Th>
            <Table.Th>Total Collection</Table.Th>
          </Table.Tr>
        </Table.Thead>

        <Table.Tbody>
          {summary.buckets.map((b) => (
            <Table.Tr key={b.label} bg={b.label === 'Total' ? 'var(--mantine-color-blue-0)' : undefined}>
              <Table.Td>{b.label}</Table.Td>
              <Table.Td>{formatNumber(b.count)}</Table.Td>
              <Table.Td>{formatCrores(b.POS)}</Table.Td>
              <Table.Td>{formatPercent(b.POS_Per)}</Table.Td>
              <Table.Td>{formatCrores(b.Post_NPA_Coll)}</Table.Td>
              <Table.Td>{formatCrores(b.Post_W_Off_Coll)}</Table.Td>
              <Table.Td>{formatCrores(b.M6_Collection)}</Table.Td>
              <Table.Td>{formatCrores(b.M12_Collection)}</Table.Td>
              <Table.Td>{formatCrores(b.total_collection)}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </div>
  );
}
