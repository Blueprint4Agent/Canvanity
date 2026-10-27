import { apiClient, getAuthHeader } from "../http";
import type { components } from "../generated/openapi";

export type BoardSummary = components["schemas"]["BoardSummary"];
export type BoardHome = components["schemas"]["BoardHomeResponse"];
export type BoardPage = components["schemas"]["BoardPageResponse"];
export type BoardCreateInput = components["schemas"]["BoardCreateForm"];
export class BoardRequestError extends Error {
    constructor(public readonly code: string) {
        super(code);
    }
}
function reject(error: unknown): never {
    if (error && typeof error === "object" && "detail" in error) {
        const detail = error.detail;
        if (
            detail &&
            typeof detail === "object" &&
            "error" in detail &&
            typeof detail.error === "string"
        )
            throw new BoardRequestError(detail.error);
        if (Array.isArray(detail)) throw new BoardRequestError("BOARD_INVALID_INPUT");
    }
    throw new BoardRequestError("BOARD_UNAVAILABLE");
}
export async function listBoards(
    q: string,
    mine: boolean,
    cursor: string | undefined,
    signal: AbortSignal,
): Promise<BoardPage> {
    const { data, error } = await apiClient.GET("/api/v1/boards", {
        headers: getAuthHeader(),
        params: { query: { q, mine, cursor, limit: 6 } },
        signal,
        cache: "no-store",
    });
    if (error || !data) reject(error);
    return data;
}
export async function getBoardHome(slug: string, signal: AbortSignal): Promise<BoardHome> {
    const { data, error } = await apiClient.GET("/api/v1/boards/by-slug/{slug}", {
        headers: getAuthHeader(),
        params: { path: { slug } },
        signal,
        cache: "no-store",
    });
    if (error || !data) reject(error);
    return data;
}
export async function createBoard(
    body: BoardCreateInput,
    signal: AbortSignal,
): Promise<BoardSummary> {
    const { data, error } = await apiClient.POST("/api/v1/boards", {
        headers: getAuthHeader(),
        body,
        signal,
    });
    if (error || !data) reject(error);
    return data;
}
export async function deleteEmptyBoard(
    id: string,
    revision: number,
    slug: string,
    signal: AbortSignal,
): Promise<void> {
    const { error } = await apiClient.DELETE("/api/v1/boards/{board_id}", {
        headers: getAuthHeader(),
        params: { path: { board_id: id } },
        body: { expected_revision: revision, confirm_slug: slug },
        signal,
    });
    if (error) reject(error);
}
