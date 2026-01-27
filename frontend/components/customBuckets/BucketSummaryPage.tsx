import { useEffect, useState } from "react";
import { BucketSidebar } from "./BucketSidebar";
import { BucketSummaryTable } from "./BucketSummaryTable";
import BucketConfigDrawer  from "./BucketConfigDrawer";
import { useBucketConfigs } from "@/hooks/useBucketConfigs";
import { mappingService } from "@/src/api/mappingService";
import { ColumnInfo } from "@/src/types/mappings";
import { bucketService } from "@/src/api/customBucketService";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@mantine/core";
import { saveAs } from "file-saver";



type Props = {
  datasetId: string;  // parent will pass this
  pageFilters?:any,
  fileType:string
};

export default function CustomBucketSummaryPage({ datasetId,pageFilters,fileType }: Props) {

  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showEmpty, setShowEmpty] = useState(true);
  const [useFilters, setFilterUse] = useState(true);
  const [drawerId, setDrawerId] = useState<string | null>(null);
  const [targetFields, setTargetFields] = useState<ColumnInfo[]>([]);
  useEffect(() => {
      (async () => {
        //We want extra's as well mod hvb @ 04/12/2025
        //const res = await mappingService.getFields();
        const res = await bucketService.getSummaryFields(datasetId);
        setTargetFields(res);
      })();
    }, [datasetId]);

  // Load bucket configs for editing
    const { data: bucketConfigs = [] } = useBucketConfigs(datasetId);

    // Load target fields list
    // const { data: targetFields = [] } = useTargetFields(datasetId);

  if (!datasetId) return null;

    // Find config for editing OR null for create
  const initialConfig =
    drawerId && drawerId !== "new"
      ? bucketConfigs.find((c) => c.id === drawerId) ?? null
      : null;


  // added by jainil -- excel file of all buckets
  const handleExportAllBuckets = async () => {
  try {
    const blob = await bucketService.exportExcel(datasetId, {
     
      config_ids:
        bucketConfigs && bucketConfigs.length > 0
          ? bucketConfigs.map((c) => c.id)
          : undefined,

    
      filters:
        Array.isArray(pageFilters) && pageFilters.length > 0
          ? pageFilters
          : undefined,

      show_empty_buckets: showEmpty ?? true,
    });

    saveAs(blob, "all_bucket_summaries.xlsx");
  } catch (err) {
    console.error("Export failed", err);
  }
};





  return (
    <div style={{ display: "flex", height: "50vh" }}>
      <BucketSidebar
        datasetId={datasetId}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onCreate={() => setDrawerId("new")}
        onEdit={setDrawerId} // passes configId
      />

      <div style={{ flex: 1 }}>
        <div style={{ padding: "8px 12px", display: "flex", justifyContent: "flex-end" }}>
          <Button
            variant="outline"
            disabled={!selectedId}
            onClick={handleExportAllBuckets}
          >
            Download all Buckets
          </Button>
        </div>

        <BucketSummaryTable
          datasetId={datasetId as string}
          configId={selectedId}
          filters={pageFilters} // reserved for future use
          showEmpty={showEmpty}
          onToggleEmpty={() => setShowEmpty((v) => !v)}
          useFilters={useFilters}
          onToggleUseFilters={()=> setFilterUse((f)=>!f)}
        />
      </div>

       {/* NEW UPDATED DRAWER */}
      <BucketConfigDrawer
        opened={!!drawerId}
        onClose={(updated) => {
          setDrawerId(null);

          if (updated && initialConfig?.id) {
            setSelectedId(initialConfig.id);
          }

          if (updated) {
            queryClient.invalidateQueries({ queryKey: ["bucket-configs", datasetId] });
            queryClient.invalidateQueries({ queryKey: ["bucket-summaries", datasetId] });
          }
        }}
        datasetId={datasetId}
        initialConfig={initialConfig}
        //Mod hvb @ 05/12/2025
        // targetFields={targetFields.map(c=>c.column_name)}
        targetFields={targetFields}
        datasetFileType={fileType}
      />
    </div>
  );
}
