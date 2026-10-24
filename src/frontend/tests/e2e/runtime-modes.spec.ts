import { captureVisual } from "../fixtures/visual";
import { expect, test } from "../fixtures/browser";
import { setup } from "../fixtures/runtime";
for (const width of [390, 1440])
    for (const colorScheme of ["light", "dark"] as const) {
        test(`production manager uses read-only directory ${colorScheme} at ${width}`, async ({
            page,
        }, info) => {
            await page.setViewportSize({ width, height: 1000 });
            await page.emulateMedia({ colorScheme });
            await setup(page, "manager");
            await page.goto("/admin");
            await expect(page.getByRole("table")).toBeVisible();
            await expect(page.getByRole("status").filter({ hasText: /^Manager$/ })).toBeVisible();
            await expect(page.getByRole("link", { name: "GitHub", exact: true })).toHaveCount(0);
            await expect(page.getByRole("link", { name: "User guide", exact: true })).toHaveCount(
                0,
            );
            await expect(page.locator('a[href="/show-case"]')).toHaveCount(0);
            await expect(
                page.getByRole("button", { name: "All roles", exact: true }),
            ).toBeVisible();
            await page.getByRole("button", { name: "All roles", exact: true }).click();
            await page.getByRole("menuitem", { name: "Manager", exact: true }).click();
            expect(
                await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            ).toBe(true);
            await captureVisual(page, {
                path: info.outputPath("production-manager.png"),
                animations: "disabled",
                fullPage: true,
            });
            for (const path of ["/show-case", "/show-case/loading", "/show-case/404"]) {
                await page.goto(path);
                await expect(page).toHaveURL(/\/home$/);
                await expect(page.locator(".showcase-catalog")).toHaveCount(0);
            }
        });
    }
test("production guest home and authentication have no showcase backdrop", async ({ page }) => {
    await setup(page, null);
    await page.goto("/show-case");
    await expect(page).toHaveURL(/\/home$/);
    await page.locator(".profile-menu__trigger").click();
    await page.getByRole("link", { name: "Log in", exact: true }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.locator(".showcase-catalog")).toHaveCount(0);
});
test("normal users cannot enter manager directory", async ({ page }) => {
    await setup(page, "user");
    await page.goto("/admin");
    await expect(page).toHaveURL(/\/home$/);
    await expect(page.getByRole("table")).toHaveCount(0);
});
test("unknown runtime mode does not enable developer UI", async ({ page }) => {
    await setup(page, null, "unknown");
    await page.goto("/show-case");
    await expect(page.locator(".showcase-catalog")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /retry|try again/i })).toBeVisible();
});
for (const width of [390, 1440]) {
    test(`main template showcase supports grid, actions and extra content at ${width}`, async ({
        page,
    }, info) => {
        await page.setViewportSize({ width, height: 1000 });
        await setup(page, "user", "development");
        await page.goto("/show-case");
        const demo = page.locator('[data-component="MainPageTemplate"]');
        await demo.scrollIntoViewIfNeeded();
        await expect(demo.locator(".main-page-template__menu--grid")).toBeVisible();
        await expect(
            demo.getByRole("heading", { name: "Content area", exact: true }),
        ).toBeVisible();
        await demo.getByRole("button", { name: "Sample action", exact: true }).click();
        await expect(
            page.getByText("Connect this action to your workflow.", { exact: true }),
        ).toBeVisible();
        const cards = await demo.locator(".main-page-template__link").evaluateAll((nodes) =>
            nodes.map((node) => ({
                x: node.getBoundingClientRect().x,
                y: node.getBoundingClientRect().y,
            })),
        );
        if (width === 390) expect(cards[1].y).toBeGreaterThan(cards[0].y);
        else expect(cards[1].x).toBeGreaterThan(cards[0].x);
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
            true,
        );
        await captureVisual(demo, {
            animations: "disabled",
            path: info.outputPath("template-showcase.png"),
        });
    });
}
for (const mode of ["development", "production"])
    test(`${mode} keeps existing resources and minimal navigation`, async ({ page }) => {
        await setup(page, "user", mode);
        await page.goto("/home");
        await expect(page.locator(".explore-page")).toBeVisible();
        const coffee = page.getByRole("link", { name: "Buy Me a Coffee" });
        await expect(coffee).toHaveCount(mode === "development" ? 1 : 0);
        await page.locator(".profile-menu__trigger").click();
        const showcase = page.getByRole("link", { name: "Showcase", exact: true });
        if (mode === "development") {
            await showcase.click();
            await expect(page.locator(".showcase-catalog")).toBeVisible();
            await page.locator(".minimal-header__brand").click();
            await expect(page).toHaveURL(/\/home$/);
        } else await expect(showcase).toHaveCount(0);
    });
for (const preview of ["topnav", "focused", "invalid"]) {
    test(`production ignores stored layout preview ${preview}`, async ({ page }) => {
        // Given: a stored development selection from a previous session.
        await page.addInitScript(
            (value) => localStorage.setItem("blueprint_layout_preview", value),
            preview,
        );
        await setup(page, "user", "production");
        // When: opening production Appearance.
        await page.goto("/settings?section=appearance");
        // Then: use the configured default and expose no development selector.
        await expect(page.locator(".app-shell")).toHaveAttribute("data-layout", "focused");
        await expect(page.getByRole("group", { name: "Layout", exact: true })).toHaveCount(0);
    });
}
for (const mode of ["topnav", "focused"]) {
    test(`${mode} guest navigation keeps login and public settings reachable`, async ({ page }) => {
        // Given: a narrow, signed-out development service.
        await page.setViewportSize({ width: 390, height: 844 });
        await page.addInitScript(
            (value) => localStorage.setItem("blueprint_layout_preview", value),
            mode,
        );
        await setup(page, null, "development");
        // When: opening the account menu and navigating to settings.
        await page.goto("/home");
        await page.locator(".profile-menu__trigger").click();
        await page
            .getByRole("dialog", { name: "Profile menu" })
            .getByRole("link", { name: "Settings", exact: true })
            .click();
        await expect(page.locator(".settings-content-card h1")).toBeVisible();
        // Then: private section links are absent and login remains available.
        if (await page.locator(".section-navigation__toggle").isVisible())
            await page.locator(".section-navigation__toggle").click();
        await expect(
            page.locator(".section-navigation").getByRole("link", { name: "Account", exact: true }),
        ).toHaveCount(0);
        await page.locator(".profile-menu__trigger").click();
        await page
            .getByRole("dialog", { name: "Profile menu" })
            .getByRole("link", { name: "Log in", exact: true })
            .click();
        await expect(page.locator(".auth-dialog")).toBeVisible();
        await expect(page.locator(".app-shell")).toHaveAttribute("data-layout", "focused");
    });
}
for (const mode of ["topnav", "focused"]) {
    for (const width of [390, 1440]) {
        test(`${mode} keeps Korean home profile inbox and administrator pages contained at ${width}`, async ({
            page,
        }, info) => {
            // Given: the compact/upper navigation mode with localized, role-filtered pages.
            await page.setViewportSize({ width, height: 900 });
            await page.addInitScript((value) => {
                localStorage.setItem("blueprint_layout_preview", value);
                localStorage.setItem("b4a_language", "ko");
            }, mode);
            await setup(page, "manager", "development");
            await page.route("**/api/v1/inbox?*", (route) =>
                route.fulfill({
                    json: {
                        items: [],
                        total: 0,
                        page: 1,
                        page_size: 20,
                        summary: { unread_count: 0, latest_id: 0 },
                    },
                }),
            );
            // When/Then: each page retains its own composition and the chosen chrome.
            for (const [path, selector] of [
                ["/home", ".explore-page"],
                ["/profile", ".personal-profile"],
                ["/notifications", ".inbox-page"],
                ["/admin", ".admin-content"],
                ["/settings?section=appearance", ".theme-preview-selector"],
            ]) {
                await page.goto(path);
                await expect(page.locator(selector)).toBeVisible();
                await expect(page.locator(".app-shell")).toHaveAttribute("data-layout", "focused");
                expect(
                    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
                ).toBe(true);
                if (path === "/admin") {
                    await expect(page.locator(".section-navigation")).toBeVisible();
                    await expect(page.locator('.app-header a[href="/admin/server"]')).toHaveCount(
                        0,
                    );
                    await expect(
                        page.locator('.section-navigation a[href="/admin/server"]'),
                    ).toHaveCount(0);
                }
                if (path.includes("appearance") && width < 961) {
                    const section = await page.locator(".section-navigation").boundingBox();
                    const heading = await page.locator(".settings-content-card h1").boundingBox();
                    expect(heading!.y - section!.y - section!.height).toBeLessThan(40);
                }
                await captureVisual(page, {
                    path: info.outputPath(`${path.split("?")[0].slice(1)}-ko.png`),
                    animations: "disabled",
                });
            }
        });
    }
}
