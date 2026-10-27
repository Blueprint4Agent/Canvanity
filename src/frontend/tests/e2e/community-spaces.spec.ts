import { expect, test } from "../fixtures/browser";
import { setup } from "../fixtures/runtime";
import { mockBoardDirectory } from "../fixtures/boards";
import { captureVisual } from "../fixtures/visual";

for (const width of [390, 1440])
    for (const colorScheme of ["light", "dark"] as const)
        test(`community spaces ${width} ${colorScheme}`, async ({ page }, info) => {
            await page.setViewportSize({ width, height: 1000 });
            await page.emulateMedia({ colorScheme });
            await setup(page, "manager", "development");
            await mockBoardDirectory(page);
            await page.goto("/home");
            const nav = page.getByRole("navigation", { name: "Community spaces" });
            await expect(nav.getByRole("link")).toHaveCount(3);
            const geometry = () =>
                page.locator(".explore-tools, .explore-map").evaluateAll((nodes) =>
                    nodes.map((node) => {
                        const { x, y, width, height } = node.getBoundingClientRect();
                        return { x, y, width, height };
                    }),
                );
            await expect(page.locator(".explore-minimap img")).toBeVisible();
            const plazaGeometry = await geometry();
            await expect(page.locator(".explore-world")).toHaveAttribute(
                "data-camera-moving",
                "false",
            );
            const start = await page
                .getByRole("heading", { name: "Plaza", exact: true })
                .boundingBox();
            const plazaSnapshot = await page.locator(".explore-minimap img").getAttribute("src");
            await expect(nav.locator("a svg")).toHaveCount(3);
            await nav.getByRole("link", { name: "My Canvas", exact: true }).click();
            await expect(
                page.getByRole("heading", { name: "My Canvas", exact: true }),
            ).toBeVisible();
            await expect(nav.getByRole("link", { name: "My Canvas" })).toHaveAttribute(
                "aria-current",
                "page",
            );
            await expect(page.locator(".explore-minimap img")).toBeVisible();
            await expect(page.locator(".my-canvas-identity")).toContainText("Manager");
            await expect(page.locator(".my-canvas-identity")).toContainText("manager@example.com");
            await expect(page.getByRole("link", { name: "Edit profile" })).toHaveAttribute(
                "href",
                "/profile",
            );
            await expect(page.locator(".personal-canvas-note")).toHaveCount(0);
            expect(await geometry()).toEqual(plazaGeometry);
            await expect(page.locator(".explore-world")).toHaveAttribute(
                "data-camera-moving",
                "false",
            );
            const heading = await page.locator(".community-heading h1").boundingBox();
            expect(Math.abs(heading!.x - start!.x)).toBeLessThan(1);
            expect(Math.abs(heading!.y - start!.y)).toBeLessThan(1);
            const profileSnapshot = await page.locator(".explore-minimap img").getAttribute("src");
            expect(profileSnapshot).not.toBe(plazaSnapshot);
            await captureVisual(page, { path: info.outputPath("my-canvas.png"), fullPage: true });
            await nav.getByRole("link", { name: "Board", exact: true }).click();
            await expect(page.getByRole("heading", { name: "Board", exact: true })).toBeVisible();
            await expect(page.locator(".community-board")).toHaveCount(4);
            await expect(page.locator(".explore-minimap img")).toBeVisible();
            expect(await geometry()).toEqual(plazaGeometry);
            await expect(page.locator(".explore-world")).toHaveAttribute(
                "data-camera-moving",
                "false",
            );
            const boardStart = await page
                .getByRole("heading", { name: "Board", exact: true })
                .boundingBox();
            expect(Math.abs(boardStart!.x - start!.x)).toBeLessThan(1);
            expect(Math.abs(boardStart!.y - start!.y)).toBeLessThan(1);
            expect(await page.locator(".explore-minimap img").getAttribute("src")).not.toBe(
                plazaSnapshot,
            );
            for (const img of await page.locator(".community-board img").all())
                await expect
                    .poll(() =>
                        img.evaluate(
                            (node: HTMLImageElement) => node.complete && node.naturalWidth > 0,
                        ),
                    )
                    .toBe(true);
            expect(
                await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            ).toBe(true);
            await captureVisual(page, { path: info.outputPath("board.png"), fullPage: true });
            await page.locator(".community-board").first().click();
            await expect(page).toHaveURL(/\/b\/agent-lab$/);
            await expect(
                page.getByRole("heading", { name: "에이전트 연구소", exact: true }),
            ).toBeVisible();
            const modifier = await page.evaluate(() =>
                /Mac/.test(navigator.userAgent) ? "Meta" : "Control",
            );
            await page.keyboard.press(`${modifier}+b`);
            await expect(page.locator(".profile-menu__dropdown")).toHaveCount(0);
            await page.locator(".profile-menu__trigger").hover();
            await expect(page.locator(".profile-menu__trigger")).not.toHaveAttribute(
                "aria-keyshortcuts",
            );
            await expect(page.getByRole("tooltip")).toHaveCount(0);
        });

test("scene snapshots reuse cached pixels and navigation hover only enlarges", async ({ page }) => {
    await setup(page, "manager", "development");
    await page.addInitScript(() => {
        const target = window as unknown as { canvasEncodes: number };
        target.canvasEncodes = 0;
        const original = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function (...args) {
            target.canvasEncodes++;
            return original.apply(this, args);
        };
    });
    await page.goto("/home");
    await expect(page.locator(".explore-minimap img")).toBeVisible();
    const originalImage = await page.locator(".explore-minimap img").getAttribute("src");
    const board = page.getByRole("link", { name: "Board", exact: true });
    await board.hover();
    await expect(board).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
    await expect(board).not.toHaveCSS("transform", "none");
    await page.emulateMedia({ reducedMotion: "reduce" });
    await expect(board).toHaveCSS("transform", "none");
    await board.click();
    await expect(page.getByRole("heading", { name: "Board", exact: true })).toBeVisible();
    await expect(page.locator(".explore-minimap img")).toBeVisible();
    const captures = await page.evaluate(
        () => (window as unknown as { canvasEncodes: number }).canvasEncodes,
    );
    await page.getByRole("link", { name: "Plaza", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Plaza", exact: true })).toBeVisible();
    await expect(page.locator(".explore-minimap img")).toHaveAttribute("src", originalImage!);
    // Wait beyond the debounce to detect unwanted background recaptures.
    await page.waitForTimeout(500);
    expect(
        await page.evaluate(() => (window as unknown as { canvasEncodes: number }).canvasEncodes),
    ).toBe(captures);
    await page.evaluate(() => (document.documentElement.dataset.theme = "dark"));
    await expect(page.locator(".explore-minimap img")).not.toHaveAttribute("src", originalImage!);
});

for (const [path, title] of [
    ["/home", "Plaza"],
    ["/my-canvas", "My Canvas"],
    ["/board", "Board"],
])
    test(`settings hide space navigation and brand returns to ${title}`, async ({ page }) => {
        await setup(page, "manager", "development");
        await page.goto(path);
        await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
        await page.locator(".profile-menu__trigger").click();
        await page.getByRole("link", { name: "Settings", exact: true }).click();
        await expect(page.locator(".community-navigation")).toHaveCount(0);
        await expect(page.locator(".minimal-header__brand")).toHaveAttribute("href", path);
        await page.reload();
        await expect(page.locator(".minimal-header__brand")).toHaveAttribute("href", path);
        await page.locator(".minimal-header__brand").click();
        await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
        await expect(page.locator(".community-navigation")).toBeVisible();
    });

test("administrator hides community navigation and returns to the previous Board", async ({
    page,
}) => {
    await setup(page, "manager", "development");
    await page.goto("/board");
    await expect(page.getByRole("heading", { name: "Board", exact: true })).toBeVisible();
    await page.goto("/admin");
    await expect(page.locator(".community-navigation")).toHaveCount(0);
    await expect(page.locator(".minimal-header__brand")).toHaveAttribute("href", "/board");
    await page.locator(".minimal-header__brand").click();
    await expect(page.getByRole("heading", { name: "Board", exact: true })).toBeVisible();
});

test("late authentication preserves the mounted page while replacing account-owned caches", async ({
    page,
}) => {
    await setup(page, "user", "development");
    let release!: () => void;
    const ready = new Promise<void>((resolve) => {
        release = resolve;
    });
    await page.route("**/api/v1/auth/refresh", async (route) => {
        await ready;
        await route.fulfill({ json: { access_token: "late-token", token_type: "bearer" } });
    });
    await page.goto("/show-case");
    await expect(page.locator(".showcase-catalog")).toBeVisible();
    const original = await page.locator(".showcase-catalog").elementHandle();
    release();
    await expect(page.locator(".profile-menu__avatar")).toContainText("M");
    expect(await original!.evaluate((node) => node.isConnected)).toBe(true);
});
