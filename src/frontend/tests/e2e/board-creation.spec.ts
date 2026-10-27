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
