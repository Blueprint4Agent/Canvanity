import React from "react";
import { createRoot } from "react-dom/client";
import {
    Excalidraw,
    convertToExcalidrawElements,
    restoreElements,
    CaptureUpdateAction,
} from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";
import { encode, decode } from "./adapter.mjs";

const png =
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAANUlEQVR4nGNUTX7NAAN5SUJw9qR577CKMzGQCJhoroFx8tG/BN09CUl8MPpBdTQeCAPaxwMAm0MZrT3JaOUAAAAASUVORK5CYII=";
const files = [
    { id: "image-one", dataURL: png, mimeType: "image/png", created: 1, lastRetrieved: 1 },
];
let api;
function seed(count = 1) {
    const elements = convertToExcalidrawElements(
        [
            {
                id: "text-one",
                type: "text",
                x: 100,
                y: 100,
                text: "한글 캔버스\n저장 후 다시 편집",
                fontFamily: 2,
            },
            { id: "shape-one", type: "rectangle", x: 100, y: 230, width: 200, height: 100 },
            {
                id: "image-one",
                type: "image",
                x: 420,
                y: 100,
                width: 160,
                height: 120,
                fileId: "image-one",
                status: "saved",
            },
            {
                id: "draw-one",
                type: "freedraw",
                x: 420,
                y: 250,
                width: 120,
                height: 60,
                points: [
                    [0, 0],
                    [30, 40],
                    [60, 10],
                    [120, 60],
                ],
                pressures: [0.2, 0.8, 0.5, 0.3],
                simulatePressure: false,
            },
            {
                id: "edge-one",
                type: "arrow",
                x: 320,
                y: 260,
                width: 80,
                height: 10,
                points: [
                    [0, 0],
                    [80, 10],
                ],
            },
            ...Array.from({ length: count - 1 }, (_, i) => ({
                id: `perf-${i}`,
                type: "rectangle",
                x: (i % 40) * 70,
                y: Math.floor(i / 40) * 60 + 400,
                width: 50,
                height: 40,
            })),
        ],
        { regenerateIds: false },
    );
    api.resetScene();
    api.addFiles(files);
    api.updateScene({
        elements: restoreElements(elements, null),
        appState: { viewBackgroundColor: "#F8F7F4" },
        captureUpdate: CaptureUpdateAction.IMMEDIATELY,
    });
    return elements.length;
}
window.canvanityProbe = {
    get api() {
        return api;
    },
    seed,
    exportDocument() {
        return encode(api.getSceneElements());
    },
    importDocument(document) {
        api.resetScene();
        api.addFiles(files);
        api.updateScene({
            elements: restoreElements(decode(document), null),
            captureUpdate: CaptureUpdateAction.IMMEDIATELY,
        });
    },
};
createRoot(document.getElementById("root")).render(
    React.createElement(
        "main",
        null,
        React.createElement(
            "p",
            { style: { margin: "8px" } },
            "편집 엔진 기술 검증 — 제품 저장 API에 연결하지 않은 독립 화면",
        ),
        React.createElement(
            "div",
            { style: { height: "calc(100vh - 40px)" } },
            React.createElement(Excalidraw, {
                langCode: "ko-KR",
                handleKeyboardGlobally: false,
                excalidrawAPI(value) {
                    api = value;
                },
                UIOptions: {
                    canvasActions: { loadScene: false, saveToActiveFile: false, export: false },
                },
            }),
        ),
    ),
);
