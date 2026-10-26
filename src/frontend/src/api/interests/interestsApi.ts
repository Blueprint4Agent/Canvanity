import { apiClient } from "../http";
import type { components } from "../generated/openapi";
export type InterestItem = components["schemas"]["InterestResponse"];
export async function getInterests(signal: AbortSignal): Promise<InterestItem[]> {
    const { data, error } = await apiClient.GET("/api/v1/interests", { signal });
    if (error || !data || !Array.isArray(data.items)) throw new Error("interests_unavailable");
    return data.items;
}
