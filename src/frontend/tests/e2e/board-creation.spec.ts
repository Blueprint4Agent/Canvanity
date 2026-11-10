import { expect, test } from "../fixtures/browser";
import { setup } from "../fixtures/runtime";
import { exampleBoard, exampleHome } from "../fixtures/boards";
import { captureVisual } from "../fixtures/visual";

test.use({ languagePreference: "ko" });
for (const width of [390, 1440])
    for (const colorScheme of ["light", "dark"] as const) {
        test(`board creation keeps drafts and opens a real home ${width} ${colorScheme}`, async ({
            page,
        }, info) => {
            await page.setViewportSize({ width, height: 1000 });
            await page.emulateMedia({ colorScheme });
            await setup(page, "user", "production");
            let created = false;
            let posts = 0;
            await page.route("**/api/v1/boards?*", (route) =>
                route.fulfill({
                    json: { items: created ? [exampleBoard] : [], next_cursor: null },
                }),
            );
            await page.route("**/api/v1/boards", async (route) => {
                const body = route.request().postDataJSON();
                expect(body.name).toBe("에이전트 연구소");
                expect(body.interest_ids).toHaveLength(3);
                expect(body.visibility).toBe("public");
                posts++;
                if (posts === 1)
                    return route.fulfill({
                        status: 409,
                        json: { detail: { error: "BOARD_SLUG_TAKEN", message: "Address taken" } },
                    });
                created = true;
                return route.fulfill({
                    status: 201,
                    json: { ...exampleBoard, slug: body.slug, interest_ids: body.interest_ids },
                });
            });
            await page.route("**/api/v1/boards/by-slug/*", (route) =>
                route.fulfill({ json: exampleHome({ ...exampleBoard, slug: "my-agent-lab" }) }),
            );
            await page.goto("/board");
            await expect(page.getByText("첫 보드를 만들어 보세요")).toBeVisible();
            await page.getByRole("button", { name: "보드 만들기", exact: true }).click();
            const modal = page.getByRole("dialog", { name: "보드 만들기" });
            await modal.getByLabel("보드 이름", { exact: true }).fill("에이전트 연구소");
            await modal.getByLabel("보드 주소", { exact: true }).fill("agent-lab");
            await modal.getByLabel("보드 소개", { exact: true }).fill("함께 나누는 개발 이야기");
            const interests = modal.getByRole("group", { name: "공식 관심사 목록" });
            const options = interests.getByRole("button");
            for (const index of [0, 1, 2]) await options.nth(index).click();
            await expect(options.nth(3)).toBeDisabled();
            await expect(modal.getByText("3/3")).toBeVisible();
            await captureVisual(page, {
                path: info.outputPath("create-board.png"),
                fullPage: true,
            });
            await modal.getByRole("button", { name: "보드 만들기", exact: true }).click();
            await expect(
                modal.getByText("이미 사용 중인 주소입니다. 다른 주소를 입력해 주세요."),
            ).toBeVisible();
            await expect(modal.getByLabel("보드 이름", { exact: true })).toHaveValue(
                "에이전트 연구소",
            );
            await expect(modal.getByLabel("보드 소개", { exact: true })).toHaveValue(
                "함께 나누는 개발 이야기",
            );
            await modal.getByLabel("보드 주소", { exact: true }).fill("my-agent-lab");
            await modal.getByRole("button", { name: "보드 만들기", exact: true }).click();
            await expect(page).toHaveURL(/\/b\/my-agent-lab$/);
            await expect(
                page.getByRole("heading", { name: "에이전트 연구소", exact: true }),
            ).toBeVisible();
            await expect(page.getByText("보드 개설자 · 뉴커머")).toBeVisible();
            await expect(page.getByRole("button", { name: "보드 탈퇴", exact: true })).toHaveCount(
                0,
            );
            await expect(
                page.getByRole("heading", { name: "공지사항", exact: true }),
            ).toBeVisible();
            await expect(
                page.getByRole("heading", { name: "자유 이야기", exact: true }),
            ).toBeVisible();
            await expect(page.getByText("아직 게시글이 없습니다")).toBeVisible();
            await expect(page.getByRole("link", { name: "Board", exact: true })).toHaveAttribute(
                "aria-current",
                "page",
            );
            await page.reload();
            await expect(
                page.getByRole("heading", { name: "에이전트 연구소", exact: true }),
            ).toBeVisible();
            await expect(page.locator(".explore-minimap img")).toBeVisible();
            await captureVisual(page, { path: info.outputPath("board-home.png"), fullPage: true });
            expect(posts).toBe(2);
            expect(
                await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            ).toBe(true);
        });
    }

test("public entry signs in before creation and private home does not leak data", async ({
    page,
}) => {
    await setup(page, null, "production");
    await page.goto("/board");
    await expect(page.getByRole("link", { name: "로그인하고 보드 만들기" })).toHaveAttribute(
        "href",
        "/login?next=%2Fboard",
    );
    await page.route("**/api/v1/boards/by-slug/private-board", (route) =>
        route.fulfill({
            status: 404,
            json: { detail: { error: "BOARD_NOT_FOUND", message: "Not found" } },
        }),
    );
    await page.goto("/b/private-board");
    await expect(page.getByText("보드가 없거나 접근할 수 없습니다.")).toBeVisible();
    await expect(page.getByRole("heading", { name: "공지사항" })).toHaveCount(0);
});

for (const width of [390, 1440])
    for (const colorScheme of ["light", "dark"] as const) {
        test(`public Board join and leave reload server membership at ${width}px ${colorScheme}`, async ({
            page,
        }, info) => {
            await page.setViewportSize({ width, height: 1000 });
            await page.emulateMedia({ colorScheme });
            await setup(page, "user", "production");
            let joined = false;
            let joinAttempts = 0;
            let leaveAttempts = 0;
            await page.route("**/api/v1/boards/by-slug/agent-lab", (route) => {
                const home = exampleHome({ ...exampleBoard, owner_id: 2 });
                home.membership = joined ? { ...home.membership!, role: "member" } : null;
                for (const shelf of home.shelves) {
                    shelf.capabilities.create_canvas = false;
                    shelf.capabilities.create_comment = joined && shelf.purpose === "general";
                }
                return route.fulfill({ json: home });
            });
            await page.route(`**/api/v1/boards/${exampleBoard.id}/join`, (route) => {
                joinAttempts++;
                if (joinAttempts === 1)
                    return route.fulfill({
                        status: 403,
                        json: { detail: { error: "BOARD_FORBIDDEN" } },
                    });
                joined = true;
                return route.fulfill({
                    json: {
                        role: "member",
                        status: "active",
                        grade_id: "20000000-0000-4000-8000-000000000001",
                        grade_name: "뉴커머",
                    },
                });
            });
            await page.route(`**/api/v1/boards/${exampleBoard.id}/membership`, (route) => {
                leaveAttempts++;
                if (leaveAttempts === 1)
                    return route.fulfill({
                        status: 503,
                        json: { detail: { error: "BOARD_UNAVAILABLE" } },
                    });
                joined = false;
                return route.fulfill({ status: 204 });
            });
            await page.goto("/b/agent-lab");
            await page.getByRole("button", { name: "보드 가입", exact: true }).click();
            await expect(page.getByText("이 보드에서 요청한 작업을 할 수 없습니다.")).toBeVisible();
            await page.getByRole("button", { name: "보드 가입", exact: true }).click();
            await expect(page.getByText("보드 회원 · 뉴커머")).toBeVisible();
            await expect(page.getByRole("button", { name: "보드 가입", exact: true })).toHaveCount(
                0,
            );
            await page.reload();
            await expect(page.getByText("보드 회원 · 뉴커머")).toBeVisible();
            await page.getByRole("button", { name: "보드 탈퇴", exact: true }).click();
            const dialog = page.getByRole("dialog", { name: "보드를 탈퇴할까요?" });
            await captureVisual(page, {
                path: info.outputPath("leave-membership.png"),
                fullPage: true,
            });
            await dialog.getByRole("button", { name: "취소", exact: true }).click();
            expect(leaveAttempts).toBe(0);
            await page.getByRole("button", { name: "보드 탈퇴", exact: true }).click();
            await dialog.getByRole("button", { name: "탈퇴하기", exact: true }).click();
            await expect(
                dialog.getByRole("button", { name: "탈퇴하기", exact: true }),
            ).toBeEnabled();
            await expect(dialog).toBeVisible();
            await dialog.getByRole("button", { name: "탈퇴하기", exact: true }).click();
            await expect(dialog).toHaveCount(0);
            await expect(
                page.getByRole("button", { name: "보드 가입", exact: true }),
            ).toBeVisible();
            expect(joinAttempts).toBe(2);
            expect(leaveAttempts).toBe(2);
        });
    }

test("guest Board login link preserves the same Board destination", async ({ page }) => {
    await setup(page, null, "production");
    const home = exampleHome();
    home.membership = null;
    await page.route("**/api/v1/boards/by-slug/agent-lab", (route) =>
        route.fulfill({ json: home }),
    );
    await page.goto("/b/agent-lab");
    await expect(page.getByRole("link", { name: "로그인하고 가입" })).toHaveAttribute(
        "href",
        "/login?next=%2Fb%2Fagent-lab",
    );
    await expect(page.getByRole("button", { name: "보드 탈퇴", exact: true })).toHaveCount(0);
});
