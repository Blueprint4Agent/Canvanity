import { captureVisual } from "../fixtures/visual";
import { expect, test } from "../fixtures/browser";
import { setup } from "../fixtures/runtime";
for (const width of [320, 390, 1440])
    for (const colorScheme of ["light", "dark"] as const) {
        test(`finite canvas menu ${colorScheme} ${width}`, async ({ page }, info) => {
            await page.setViewportSize({ width, height: 1000 });
            await page.emulateMedia({ colorScheme });
            await setup(page, "manager", "development");
            await page.goto("/home");
            await expect(page.locator("#home-project-title")).toBeVisible();
            await expect(page.locator(".explore-cluster")).toHaveCount(4);
            await expect(page.locator(".app-sidebar")).toHaveCount(0);
            await expect(page.locator(".app-header--minimal")).toBeVisible();
            await expect(page.getByRole("link", { name: "GitHub", exact: true })).toBeVisible();
            await expect(
                page.getByRole("link", { name: "Buy Me a Coffee", exact: true }),
            ).toBeVisible();
            const image = page.locator(".explore-minimap img");
            await expect(image).toBeVisible();
            await expect
                .poll(() =>
                    image.evaluate(
                        (img: HTMLImageElement) => img.complete && img.naturalWidth === 288,
                    ),
                )
                .toBe(true);
            expect(
                await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
            ).toBe(true);
            const grid = await page
                .locator(".explore-viewport")
                .evaluate((el) => getComputedStyle(el).backgroundImage);
            expect(grid).toContain("linear-gradient");
            expect(grid).not.toContain("radial-gradient");
            await page.keyboard.press("+");
            await expect(page.locator(".explore-zoom")).not.toHaveText("25%");
            await page.keyboard.press("/");
            await expect(page.getByRole("searchbox")).toBeFocused();
            await page.getByRole("searchbox").fill("people");
            await page.keyboard.press("Enter");
            await expect(page.locator(".explore-selection")).toContainText("people");
            await page.keyboard.press("0");
            await expect(page.locator(".explore-selection")).toHaveCount(0);
            await captureVisual(page, { path: info.outputPath("canvas.png"), fullPage: true });
        });
    }
test("camera limits, browser chord isolation, wheel and minimap use one bounded camera", async ({
    page,
}) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await setup(page, null);
    await page.goto("/home");
    const canvas = page.locator(".explore-viewport");
    await expect(canvas).toBeVisible();
    await canvas.focus();
    for (let i = 0; i < 25; i++) await page.keyboard.press("+");
    await expect(page.locator(".explore-zoom")).toHaveText("200%");
    await expect(page.getByRole("button", { name: "Zoom in", exact: true })).toBeDisabled();
    await expect(page.locator(".explore-world")).toHaveAttribute("data-camera-moving", "false");
    await page.keyboard.press("Control+-");
    await expect(page.locator(".explore-zoom")).not.toHaveText("200%");
    await expect(page.locator(".explore-world")).toHaveAttribute("data-camera-moving", "false");
    await page.mouse.move(800, 500);
    await page.mouse.wheel(50000, 50000);
    await page.waitForTimeout(50);
    const bounded = await page.locator(".explore-world").evaluate((el) => {
        const m = new DOMMatrix(getComputedStyle(el).transform);
        return { x: m.e, y: m.f };
    });
    expect(bounded.x).toBeGreaterThanOrEqual(-4960);
    expect(bounded.y).toBeGreaterThanOrEqual(-3200);
    const image = page.locator(".explore-minimap img");
    await expect(image).toBeVisible();
    const src = await image.getAttribute("src");
    await page.locator(".explore-minimap").click({ position: { x: 10, y: 10 } });
    expect(await image.getAttribute("src")).toBe(src);
    for (let i = 0; i < 35; i++) await page.keyboard.press("-");
    await expect(page.locator(".explore-zoom")).toHaveText("25%");
    await expect(
        page.locator(".explore-topic__handwriting").filter({ hasText: "The art of noticing" }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: "Zoom out", exact: true })).toBeDisabled();
    await page.getByRole("button", { name: "Zoom in", exact: true }).hover();
    await expect(page.getByRole("tooltip")).toContainText("+");
});

test("touch pinch shares finite zoom rules and minimap has no blue fill", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await setup(page, null);
    await page.goto("/home");
    await expect(page.locator(".explore-viewport")).toBeVisible();
    const session = await page.context().newCDPSession(page);
    await session.send("Emulation.setTouchEmulationEnabled", { enabled: true });
    await expect(page.locator(".explore-world")).toHaveAttribute("data-camera-moving", "false");
    const before = Number((await page.locator(".explore-zoom").innerText()).replace("%", ""));
    await session.send("Input.dispatchTouchEvent", {
        type: "touchStart",
        touchPoints: [
            { x: 150, y: 450 },
            { x: 230, y: 450 },
        ],
    });
    await session.send("Input.dispatchTouchEvent", {
        type: "touchMove",
        touchPoints: [
            { x: 90, y: 450 },
            { x: 290, y: 450 },
        ],
    });
    await session.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await expect
        .poll(async () =>
            Number((await page.locator(".explore-zoom").innerText()).replace("%", "")),
        )
        .toBeGreaterThan(before);
    await expect(page.locator(".explore-minimap__viewport")).toHaveCSS(
        "background-color",
        "rgba(0, 0, 0, 0)",
    );
    await expect(page.locator("#explore-keyboard-help")).toHaveCount(0);
    const bounds = await page.locator(".explore-page").boundingBox();
    expect(bounds?.x).toBe(0);
    expect(bounds?.width).toBe(390);
    expect(bounds?.height).toBe(900);
    await session.detach();
});

test("zoom controls animate the actual scene and respect reduced motion", async ({ page }) => {
    await setup(page, null);
    await page.goto("/home");
    await expect(page.locator(".explore-world")).toHaveAttribute("data-camera-moving", "false");
    const world = page.locator(".explore-world");
    const before = await world.evaluate((el) => new DOMMatrix(getComputedStyle(el).transform).a);
    await page.getByRole("button", { name: "Zoom in", exact: true }).click();
    await expect(page.locator(".explore-world")).toHaveAttribute("data-camera-moving", "true");
    await expect(page.locator(".explore-world")).toHaveAttribute("data-camera-moving", "false");
    const after = await world.evaluate((el) => new DOMMatrix(getComputedStyle(el).transform).a);
    expect(after).toBeCloseTo(before * 1.2, 2);
    await page.getByRole("button", { name: "Zoom out", exact: true }).click();
    await expect(world).toHaveAttribute("data-camera-moving", "false");
    expect(
        await world.evaluate((el) => new DOMMatrix(getComputedStyle(el).transform).a),
    ).toBeCloseTo(before, 2);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.getByRole("button", { name: "Zoom in", exact: true }).click();
    await expect(world).toHaveAttribute("data-camera-moving", "false");
    await expect(page.locator(".explore-local-heading")).toHaveCount(0);
});

test("plain vertical zoom tools and photo hover follow the minimal reference", async ({ page }) => {
    await setup(page, null, "development");
    await page.goto("/home");
    await expect(page.locator(".explore-world")).toHaveAttribute("data-camera-moving", "false");
    await expect(page.locator(".minimal-header__actions")).toHaveCSS(
        "background-color",
        "rgba(0, 0, 0, 0)",
    );
    await expect(page.locator(".explore-zoom-tools")).toHaveCSS("flex-direction", "column");
    await expect(page.locator(".explore-zoom-tools")).toHaveCSS(
        "background-color",
        "rgba(0, 0, 0, 0)",
    );
    await expect(page.locator(".explore-minimap")).toHaveCSS("border-top-width", "0px");
    await expect(page.locator(".explore-minimap")).toHaveCSS("box-shadow", "none");
    const topic = page.locator(".explore-cluster--daily .explore-topic");
    await topic.hover();
    await expect
        .poll(() => topic.evaluate((el) => new DOMMatrix(getComputedStyle(el).transform).a))
        .toBeGreaterThan(1.02);
    await expect(topic).toHaveCSS("text-decoration-line", "none");
    await expect(topic.locator(".ui-button__label")).toHaveCSS("text-decoration-line", "none");
});

test("trackpad pinch and browser zoom chords belong to the mounted canvas", async ({ page }) => {
    await setup(page, null);
    await page.goto("/home");
    const world = page.locator(".explore-world");
    await expect(world).toHaveAttribute("data-camera-moving", "false");
    const initial = await page.locator(".explore-zoom").innerText();
    const cancelled = await page.locator(".explore-viewport").evaluate(
        (el) =>
            !el.dispatchEvent(
                new WheelEvent("wheel", {
                    deltaY: -30,
                    ctrlKey: true,
                    clientX: 500,
                    clientY: 400,
                    bubbles: true,
                    cancelable: true,
                }),
            ),
    );
    expect(cancelled).toBe(true);
    await expect(page.locator(".explore-zoom")).not.toHaveText(initial);
    await expect(world).toHaveAttribute("data-camera-moving", "false");
    const before = await page.locator(".explore-zoom").innerText();
    await page.keyboard.press("Meta+-");
    await expect(page.locator(".explore-zoom")).not.toHaveText(before);
    const zoom = await page.locator(".explore-zoom").innerText();
    await page.mouse.move(800, 500);
    await page.mouse.wheel(100, 100);
    await expect(page.locator(".explore-zoom")).toHaveText(zoom);
    expect(await page.evaluate(() => visualViewport?.scale)).toBe(1);
});

test("Space temporarily pans, release and blur restore clicks without native text selection", async ({
    page,
}) => {
    await setup(page, null);
    await page.goto("/home");
    const world = page.locator(".explore-world");
    await expect(world).toHaveAttribute("data-camera-moving", "false");
    const transform = () => world.evaluate((el) => getComputedStyle(el).transform);
    const before = await transform();
    await page.mouse.move(800, 540);
    await page.mouse.down();
    await page.mouse.move(900, 580, { steps: 5 });
    await page.mouse.up();
    expect(await transform()).toBe(before);
    expect(await page.evaluate(() => window.getSelection()?.toString())).toBe("");
    await page.keyboard.down("Space");
    await expect(page.locator(".explore-page")).toHaveAttribute("data-tool", "hand");
    await page.mouse.move(800, 540);
    await page.mouse.down();
    await page.mouse.move(900, 580, { steps: 5 });
    await expect.poll(transform).not.toBe(before);
    await page.keyboard.up("Space");
    await expect(page.locator(".explore-page")).toHaveAttribute("data-tool", "select");
    await page.mouse.up();
    await page.keyboard.down("Space");
    await page.evaluate(() => window.dispatchEvent(new Event("blur")));
    await expect(page.locator(".explore-page")).toHaveAttribute("data-tool", "select");
    await page.keyboard.up("Space");
    await page.locator(".explore-cluster--daily button").click();
    await expect(page.locator(".explore-selection")).toContainText("spotlight");
    await page.keyboard.press("/");
    await page.getByRole("searchbox").fill("people");
    await page.keyboard.press("Space");
    await expect(page.getByRole("searchbox")).toHaveValue("people ");
    await expect(page.locator(".explore-page")).toHaveAttribute("data-tool", "select");
});

test("community feed stays composed with author comment and like metadata", async ({ page }) => {
    await setup(page, null);
    await page.goto("/home");
    await expect(page.locator("#home-project-title")).toHaveText("Canvanity");
    await expect(page.locator(".explore-cluster")).toHaveCount(4);
    await expect(page.locator(".explore-post-meta")).toHaveCount(7);
    await expect(
        page.getByRole("heading", { name: "Canvases from people you follow" }),
    ).toBeVisible();
    await expect(page.getByText("Where conversations grow", { exact: true })).toHaveCount(0);
    await expect(page.locator(".explore-tools button")).toHaveCount(1);
    const geometry = () =>
        page.locator(".explore-cluster").evaluateAll((els) =>
            els.map((el) => ({
                x: (el as HTMLElement).offsetLeft,
                y: (el as HTMLElement).offsetTop,
            })),
        );
    const before = await geometry();
    expect(new Set(before.map((p) => p.x)).size).toBe(4);
    expect(new Set(before.map((p) => p.y)).size).toBe(4);
    await expect(page.locator('.explore-post-meta [aria-label*="comments"]')).toHaveCount(7);
    const author = page.locator(".explore-post-author").first();
    await expect(author).not.toContainText("sample");
    await page.reload();
    await expect(page.locator(".explore-cluster")).toHaveCount(4);
    expect(await geometry()).toEqual(before);
});

test("canvas edge gives a tiny smooth resistance then settles inside its bounds", async ({
    page,
}) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await setup(page, null);
    await page.goto("/home");
    const world = page.locator(".explore-world");
    await expect(world).toHaveAttribute("data-camera-moving", "false");
    for (let i = 0; i < 12; i++) await page.keyboard.press("-");
    await expect(page.locator(".explore-zoom")).toHaveText("25%");
    await expect(world).toHaveAttribute("data-camera-moving", "false");
    await page.mouse.move(750, 500);
    await page.mouse.wheel(0, 500);
    await expect
        .poll(() => world.evaluate((el) => Math.abs(Number((el as HTMLElement).dataset.edgeY))))
        .toBeGreaterThan(0);
    expect(
        await world.evaluate((el) => Math.abs(Number((el as HTMLElement).dataset.edgeY))),
    ).toBeLessThanOrEqual(10);
    await expect(world).toHaveAttribute("data-camera-moving", "false");
    await expect(world).toHaveAttribute("data-edge-y", "0");
    const logical = await world.evaluate((el) => Number((el as HTMLElement).dataset.logicalY));
    expect(logical).toBe(237.5);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.mouse.wheel(0, 500);
    await expect(world).toHaveAttribute("data-edge-y", "0");
});
