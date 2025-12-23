import { useQuery } from "@tanstack/react-query";
import { bucketService } from "@/src/api/customBucketService";
import { BucketConfigListItem } from "@/src/types/custombucket";

export function useBucketConfigs(datasetId?: string | null) {
  return useQuery<BucketConfigListItem[]>({
    queryKey: ["bucket-configs", datasetId],
    queryFn: ({ signal }) =>
      bucketService.list(datasetId!, signal),
    enabled: !!datasetId,
    staleTime: 5 * 60 * 1000,
  });
}

