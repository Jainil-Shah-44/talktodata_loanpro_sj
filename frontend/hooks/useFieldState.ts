import { useQuery } from "@tanstack/react-query";
import { fieldsService } from "@/src/api/fieldsService";
import { ColumnStatRequest, ColumnStatsResponse } from "@/src/types/fieldsService";

export function useFieldState(
    request: ColumnStatRequest | null,
    enabled: boolean = true
) {
    return useQuery<ColumnStatsResponse | undefined>({
        queryKey: ["field-stats", request?.pk_id, request?.column_name],
        queryFn: async ({ signal }) => {
            if (!request) return undefined;
            return await fieldsService.stats(request, signal);
        },

        enabled: enabled && !!request,

        // cache/stale behavior
        staleTime: 60 * 1000,      // 1 minute before refetching
        gcTime: 5 * 60 * 1000,     // keep cached for 5 minutes

        // when data comes back, keeps stable structure
        select: (data) => data,

        retry: 1, // prevent spam retries for DB/min-max queries
        refetchOnWindowFocus: false, // avoid unnecessary refetches
    });
}
