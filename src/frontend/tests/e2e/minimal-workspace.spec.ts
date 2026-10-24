import { expect, test } from "../fixtures/browser";
import { setup } from "../fixtures/runtime";
import { captureVisual } from "../fixtures/visual";

for (const width of [390, 1440])
    for (const theme of ["light", "dark"] as const)
        test(`minimal workspace ${theme} ${width}`, async ({ page }, info) => {
            await page.setViewportSize({ width, height: 1000 });
            await page.emulateMedia({ colorScheme: theme });
            await setup(page, "admin", "development");
            for (const route of [
                "/settings?section=account",
                "/settings?section=general",
                "/admin",
            ]) {
                await page.goto(route);
                await expect(page.locator(".settings-content-card h1")).toBeVisible();
                const nav = page.locator(".section-navigation");
                const content = page.locator(".settings-content-card");
                const navRect = (await nav.boundingBox())!;
                const contentRect = (await content.boundingBox())!;
                if (width > 640) {
                    expect(contentRect.x).toBeGreaterThan(navRect.x + navRect.width);
                    await expect(nav.locator(".section-navigation__editorial")).toBeVisible();
                } else {
                    expect(contentRect.y).toBeGreaterThan(navRect.y + navRect.height);
                    await expect(nav.locator(".section-navigation__editorial")).toBeHidden();
                }
                await expect(content).toHaveCSS("border-radius", "0px");
                expect(
                    await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
                ).toBe(true);
                const grid = await page
                    .locator(".app-main")
                    .evaluate((el) => getComputedStyle(el).backgroundImage);
                expect(grid).toContain("linear-gradient");
                await captureVisual(page, {
                    path: info.outputPath(
                        `${route.startsWith("/admin") ? "admin" : route.split("=")[1]}.png`,
                    ),
                    fullPage: true,
                });
            }
        });

test("Showcase canvas variants share hover, focus, disabled and reduced motion", async ({
    page,
}) => {
    await setup(page, "admin", "development");
    await page.goto("/show-case");
    await page.getByRole("searchbox", { name: "Find a component" }).fill("Button (canvas");
    const card = page.locator(".showcase-canvas-card");
    await card.hover();
    await expect
        .poll(() => card.evaluate((el) => new DOMMatrix(getComputedStyle(el).transform).a))
        .toBeCloseTo(1.025, 3);
    await expect(card).toHaveCSS("text-decoration-line", "none");
    const actions = page.locator('[data-component="Button (canvas actions)"]');
    await expect(actions.locator("button:disabled")).toHaveCount(2);
    const icon = actions.locator(".ui-button--icon");
    await page.mouse.move(0, 0);
    await icon.focus();
    await expect(icon).toBeFocused();
    await expect(icon).toHaveCSS("outline-style", "solid");
    await expect(icon).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
    await page.emulateMedia({ reducedMotion: "reduce" });
    await card.hover();
    await expect(card).toHaveCSS("transform", "none");
    expect(
        await card.evaluate((el) => parseFloat(getComputedStyle(el).transitionDuration)),
    ).toBeLessThan(0.001);
});

test("local navigation stays fixed while settings content scrolls and headings use sans", async ({
    page,
}) => {
    await page.setViewportSize({ width: 1440, height: 600 });
    await setup(page, "admin", "development");
    await page.goto("/settings?section=account");
    const nav = page.locator(".section-navigation");
    await expect(nav).toHaveCSS("position", "sticky");
    const before = (await nav.boundingBox())!.y;
    await page.mouse.move(1000, 420);
    await page.mouse.wheel(0, 400);
    await expect
        .poll(() => page.locator(".app-main").evaluate((el) => el.scrollTop))
        .toBeGreaterThan(0);
    expect(Math.abs((await nav.boundingBox())!.y - before)).toBeLessThan(1);
    const heading = page.locator(".settings-content-card h1");
    expect(await heading.evaluate((el) => getComputedStyle(el).fontFamily)).not.toMatch(
        /Caveat|Nanum Pen/,
    );
    const active = nav.locator('[aria-current="page"]');
    expect(await active.evaluate((el) => getComputedStyle(el, "::before").maskImage)).toContain(
        "pencil-highlight.svg",
    );
});

test("shared card appearance preserves finite home card geometry", async ({ page }) => {
    await setup(page, null, "development");
    await page.goto("/home");
    const topic = page.locator(".explore-cluster--daily .explore-topic");
    await expect(topic).toHaveCSS("height", "340px");
    const photo = (await topic.boundingBox())!;
    const following = (await page.locator(".explore-cluster--agent header").boundingBox())!;
    expect(following.y).toBeGreaterThan(photo.y + photo.height + 20);
});

test("capsule variants keep their shape and shortcut hover paints one surface", async ({
    page,
}) => {
    await setup(page, "admin", "development");
    await page.goto("/show-case");
    await page.getByRole("searchbox", { name: "Find a component" }).fill("Button (pill variants)");
    const pill = page.locator('[data-component="Button (pill variants)"] .ui-button--pill').first();
    const box = (await pill.boundingBox())!;
    expect(
        await pill.evaluate((el) => parseFloat(getComputedStyle(el).borderRadius)),
    ).toBeGreaterThan(box.height / 2);
    await pill.hover();
    await expect(pill).not.toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
    await page.goto("/settings?section=keyboard");
    const shortcut = page.locator(".settings-shortcut-trigger").first();
    const before = (await shortcut.boundingBox())!;
    await shortcut.hover();
    await expect(shortcut.locator("kbd")).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
    await expect(shortcut).not.toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
    expect((await shortcut.boundingBox())!.height).toBe(before.height);
});
