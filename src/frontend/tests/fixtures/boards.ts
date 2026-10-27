import type { components } from "../../src/api/generated/openapi";
import type { Page } from "./browser";
export const exampleBoard: components["schemas"]["BoardSummary"] = {
    id: "10000000-0000-4000-8000-000000000001",
    owner_id: 1,
    name: "에이전트 연구소",
    slug: "agent-lab",
    description: "에이전트 설계와 개발 경험을 공유합니다.",
    visibility: "public",
    join_policy: "open",
    status: "active",
    revision: 0,
    interest_ids: ["ai"],
    created_at: "2026-10-26T00:00:00Z",
};
export function exampleHome(board = exampleBoard): components["schemas"]["BoardHomeResponse"] {
    const grades = ["뉴커머", "피너", "큐레이터"].map((name, index) => ({
        id: `20000000-0000-4000-8000-00000000000${index + 1}`,
        name,
        rank: index * 10,
        is_default: index === 0,
    }));
    return {
        board,
        rules: "",
        membership: {
            role: "owner",
            status: "active",
            grade_id: grades[0].id,
            grade_name: "뉴커머",
        },
        grades,
        shelves: ["공지사항", "자유 이야기"].map((name, index) => ({
            id: `30000000-0000-4000-8000-00000000000${index + 1}`,
            slug: index ? "general" : "notice",
            name,
            description: "",
            icon: index ? "messages-square" : "megaphone",
            purpose: index ? "general" : "notice",
            classification: "manual",
            sort_order: index,
            is_default: !!index,
            capabilities: {
                read_canvas: true,
                create_canvas: true,
                create_comment: true,
                react: true,
            },
        })),
        layout: { schema_version: 1, widgets: [] },
        layout_revision: 0,
    };
}
export async function mockBoardDirectory(page: Page) {
    const boards = [
        exampleBoard,
        ...["읽고 나누는 책장", "사진과 일상", "함께 만드는 것들"].map((name, index) => ({
            ...exampleBoard,
            id: `10000000-0000-4000-8000-00000000000${index + 2}`,
            slug: `sample-${index}`,
            name,
        })),
    ];
    await page.route("**/api/v1/boards?*", (route) =>
        route.fulfill({ json: { items: boards, next_cursor: null } }),
    );
    await page.route("**/api/v1/boards/by-slug/*", (route) => {
        const slug = new URL(route.request().url()).pathname.split("/").at(-1);
        return route.fulfill({
            json: exampleHome(boards.find((board) => board.slug === slug) ?? exampleBoard),
        });
    });
}
