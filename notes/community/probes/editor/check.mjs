import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const output = fileURLToPath(new URL("../../../../.git/community-probes/", import.meta.url));
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const checks = [],
    errors = [],
    timings = [];
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.on("pageerror", (error) => errors.push(error.message));
await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    return ["127.0.0.1", "localhost"].includes(url.hostname) ||
        ["data:", "blob:"].includes(url.protocol)
        ? route.continue()
        : route.abort();
});
async function check(name, action) {
    try {
        await action();
        checks.push({ name, status: "passed" });
    } catch (error) {
        checks.push({ name, status: "failed", error: error.message.slice(0, 400) });
    }
}
try {
    await page.goto("http://127.0.0.1:5193", { waitUntil: "networkidle" });
    await page.waitForFunction(() => window.canvanityProbe?.api);
    await check("five_element_adapter_round_trip", async () => {
        await page.evaluate(() => window.canvanityProbe.seed());
        await page.waitForFunction(() => window.canvanityProbe.api.getSceneElements().length === 5);
        await page.evaluate(
            () =>
                new Promise((resolve) =>
                    requestAnimationFrame(() => requestAnimationFrame(resolve)),
                ),
        );
        const before = await page.evaluate(() => window.canvanityProbe.exportDocument());
        assert.deepEqual(before.nodes.map((x) => x.type).sort(), [
            "drawing",
            "image",
            "shape",
            "text",
        ]);
        assert.equal(before.edges.length, 1);
        assert(!JSON.stringify(before).includes("data:image"));
        assert(!JSON.stringify(before).includes("selectedElementIds"));
        await page.evaluate(
            (document) =>
                window.canvanityProbe.importDocument(JSON.parse(JSON.stringify(document))),
            before,
        );
        await page.waitForFunction(() => window.canvanityProbe.api.getSceneElements().length === 5);
        await page.evaluate(
            () =>
                new Promise((resolve) =>
                    requestAnimationFrame(() => requestAnimationFrame(resolve)),
                ),
        );
        const after = await page.evaluate(() => window.canvanityProbe.exportDocument());
        assert.deepEqual(after, before);
        assert.equal(
            await page.evaluate(() => Object.keys(window.canvanityProbe.api.getFiles()).length),
            1,
        );
        await page.screenshot({ path: output + "editor-desktop.png" });
    });
    await check("korean_multiline_edit_and_shortcut_text", async () => {
        await page.evaluate(() => {
            window.canvanityProbe.api.resetScene();
            window.canvanityProbe.api.setActiveTool({ type: "text" });
        });
        await page.mouse.click(350, 320);
        const input = page.locator("textarea.excalidraw-wysiwyg");
        await input.waitFor({ state: "visible" });
        await page.keyboard.insertText("한글 조합 검증\n두 번째 줄 / v +");
        // 합성 composition은 이벤트 전달 검사이며 운영체제 IME 검증이 아니다.
        await input.dispatchEvent("compositionstart", { data: "ㅎ" });
        await input.dispatchEvent("compositionupdate", { data: "한" });
        await input.dispatchEvent("compositionend", { data: "한" });
        await page.keyboard.press("Escape");
        await page.waitForFunction(() =>
            window.canvanityProbe.api
                .getSceneElements()
                .some((x) => x.type === "text" && x.text.includes("두 번째 줄 / v +")),
        );
        const saved = await page.evaluate(() => window.canvanityProbe.exportDocument());
        await page.evaluate((document) => window.canvanityProbe.importDocument(document), saved);
        assert(
            (
                await page.evaluate(() => window.canvanityProbe.api.getSceneElements()[0].text)
            ).includes("한글 조합 검증"),
        );
    });
    await check("pointer_draw_undo_redo", async () => {
        await page.evaluate(() => {
            window.canvanityProbe.api.resetScene();
            window.canvanityProbe.api.setActiveTool({ type: "freedraw" });
        });
        await page.mouse.move(400, 400);
        await page.mouse.down();
        await page.mouse.move(470, 450, { steps: 8 });
        await page.mouse.move(530, 410, { steps: 8 });
        await page.mouse.up();
        await page.waitForFunction(() =>
            window.canvanityProbe.api.getSceneElements().some((x) => x.type === "freedraw"),
        );
        const shortcut = process.platform === "darwin" ? "Meta" : "Control";
        await page.keyboard.press(shortcut + "+z");
        await page.waitForFunction(() => window.canvanityProbe.api.getSceneElements().length === 0);
        await page.keyboard.press(shortcut + "+Shift+z");
        await page.waitForFunction(() =>
            window.canvanityProbe.api.getSceneElements().some((x) => x.type === "freedraw"),
        );
    });
    await check("image_file_drop", async () => {
        await page.evaluate(() => window.canvanityProbe.api.resetScene());
        await page.evaluate(async () => {
            const blob = await (
                await fetch(
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAANUlEQVR4nGNUTX7NAAN5SUJw9qR577CKMzGQCJhoroFx8tG/BN09CUl8MPpBdTQeCAPaxwMAm0MZrT3JaOUAAAAASUVORK5CYII=",
                )
            ).blob();
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(new File([blob], "probe.png", { type: "image/png" }));
            document.querySelector(".excalidraw").dispatchEvent(
                new DragEvent("drop", {
                    bubbles: true,
                    cancelable: true,
                    clientX: 400,
                    clientY: 400,
                    dataTransfer,
                }),
            );
        });
        await page.waitForFunction(
            () => window.canvanityProbe.api.getSceneElements().some((x) => x.type === "image"),
            { timeout: 10000 },
        );
    });
    await check("image_clipboard_paste", async () => {
        await page.evaluate(() => window.canvanityProbe.api.resetScene());
        await page.locator(".excalidraw").click({ position: { x: 600, y: 500 } });
        await page.evaluate(async () => {
            // 실제 OS 클립보드 대신 공개 PNG 파일 fixture를 전달한다.
            const blob = await (
                await fetch(
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAANUlEQVR4nGNUTX7NAAN5SUJw9qR577CKMzGQCJhoroFx8tG/BN09CUl8MPpBdTQeCAPaxwMAm0MZrT3JaOUAAAAASUVORK5CYII=",
                )
            ).blob();
            const clipboardData = new DataTransfer();
            clipboardData.items.add(new File([blob], "clipboard.png", { type: "image/png" }));
            document
                .querySelector(".excalidraw")
                .dispatchEvent(
                    new ClipboardEvent("paste", { bubbles: true, cancelable: true, clipboardData }),
                );
        });
        await page.waitForFunction(
            () => window.canvanityProbe.api.getSceneElements().some((x) => x.type === "image"),
            null,
            { timeout: 10000 },
        );
    });
    await check("reload_saved_canonical_document", async () => {
        await page.evaluate(() => {
            window.canvanityProbe.seed();
        });
        await page.evaluate(
            () =>
                new Promise((resolve) =>
                    requestAnimationFrame(() => requestAnimationFrame(resolve)),
                ),
        );
        const before = await page.evaluate(() => {
            const document = window.canvanityProbe.exportDocument();
            localStorage.setItem("probe-document", JSON.stringify(document));
            return document;
        });
        await page.reload({ waitUntil: "networkidle" });
        await page.waitForFunction(() => window.canvanityProbe?.api);
        await page.evaluate(() =>
            window.canvanityProbe.importDocument(
                JSON.parse(localStorage.getItem("probe-document")),
            ),
        );
        await page.evaluate(
            () =>
                new Promise((resolve) =>
                    requestAnimationFrame(() => requestAnimationFrame(resolve)),
                ),
        );
        assert.deepEqual(await page.evaluate(() => window.canvanityProbe.exportDocument()), before);
        await page.evaluate(() => localStorage.removeItem("probe-document"));
    });
    await check("100_1000_element_encode_restore_timing", async () => {
        for (const count of [96, 996]) {
            const result = await page.evaluate(async (count) => {
                const start = performance.now();
                const elements = window.canvanityProbe.seed(count);
                await new Promise((resolve) =>
                    requestAnimationFrame(() => requestAnimationFrame(resolve)),
                );
                const mounted = performance.now();
                const doc = window.canvanityProbe.exportDocument();
                const serialized = JSON.stringify(doc);
                const exported = performance.now();
                window.canvanityProbe.importDocument(JSON.parse(serialized));
                await new Promise((resolve) =>
                    requestAnimationFrame(() => requestAnimationFrame(resolve)),
                );
                return {
                    elements,
                    bytes: new TextEncoder().encode(serialized).length,
                    mount_to_two_frames_ms: mounted - start,
                    encode_ms: exported - mounted,
                    restore_to_two_frames_ms: performance.now() - exported,
                };
            }, count);
            assert.equal(result.elements, count + 4);
            timings.push(result);
        }
    });
    await check("mobile_touch_context_render", async () => {
        const context = await browser.newContext({
            viewport: { width: 390, height: 844 },
            isMobile: true,
            hasTouch: true,
        });
        const mobile = await context.newPage();
        await mobile.goto("http://127.0.0.1:5193", { waitUntil: "networkidle" });
        await mobile.waitForFunction(() => window.canvanityProbe?.api);
        await mobile.evaluate(() => window.canvanityProbe.seed());
        await mobile.touchscreen.tap(210, 450);
        await mobile.screenshot({ path: output + "editor-mobile.png" });
        assert.equal(
            await mobile.evaluate(() => window.canvanityProbe.api.getSceneElements().length),
            5,
        );
        await context.close();
    });
    await check("no_page_runtime_errors", async () => assert.deepEqual(errors, []));
} finally {
    await browser.close();
}
const report = {
    engine: "@excalidraw/excalidraw@0.18.1",
    react: "18.3.1",
    browser: "headless Chromium",
    viewport: "1440x1000 + 390x844 touch",
    checks,
    timings,
    limitations: [
        "OS-native Korean IME and physical pen pressure are not verified",
        "No product API, authorization or server persistence is connected",
        "Two-frame latency is a local probe, not FPS or product performance guarantee",
        "Image upload is an in-memory fixture, not object storage integration",
    ],
};
await writeFile(output + "editor.json", JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
if (checks.some((check) => check.status === "failed")) process.exitCode = 1;
