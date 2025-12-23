import { useQuery } from "@tanstack/react-query";
import { bucketService } from "@/src/api/customBucketService";
import {
  BucketSummaryRequest,
  BucketSummaryResponse,
} from "@/src/types/custombucket";

export function useBucketSummaries(
  datasetId: string,
  payload: BucketSummaryRequest | null,
  useFilters: boolean
) {
  return useQuery<BucketSummaryResponse[]>({
    queryKey: ["bucket-summaries", datasetId, payload,useFilters],
    enabled: !!payload,
    queryFn: async ({ signal }) =>
      await bucketService.getSummaries(datasetId, payload!, signal),
      staleTime: 0,
      refetchOnWindowFocus: false,
  });
}
