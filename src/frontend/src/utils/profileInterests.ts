import type { components } from "../api/generated/openapi";
export type InterestItem = components["schemas"]["InterestResponse"];
export function interestLabel(id: string, items: InterestItem[], language: string): string {
    const item = items.find((value) => value.id === id);
    return item ? (language.startsWith("ko") ? item.name_ko : item.name_en) : id;
}
