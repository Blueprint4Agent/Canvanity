// 검증 전용 어댑터. 서버 validator/업로드 API를 대신하지 않는다.
const types = {
    text: "text",
    image: "image",
    freedraw: "drawing",
    rectangle: "shape",
    ellipse: "shape",
    diamond: "shape",
};
export function encode(elements) {
    const nodes = [],
        edges = [];
    for (const input of elements.filter((element) => !element.isDeleted)) {
        const element = JSON.parse(JSON.stringify(input));
        // 외부 URL과 바이너리는 영속 문서에 넣지 않는다.
        delete element.link;
        const asset_id = element.type === "image" ? `probe-asset-${element.fileId}` : undefined;
        delete element.fileId;
        const base = {
            id: element.id,
            position: { x: element.x, y: element.y },
            size: { width: element.width, height: element.height },
            engine_element: element,
        };
        if (element.type === "arrow" || element.type === "line") {
            edges.push({
                ...base,
                type: "edge",
                source_node_id: element.startBinding?.elementId ?? null,
                target_node_id: element.endBinding?.elementId ?? null,
            });
        } else {
            if (!types[element.type]) throw new Error(`검증 범위 밖 요소: ${element.type}`);
            nodes.push({
                ...base,
                type: types[element.type],
                ...(asset_id ? { content: { asset_id } } : {}),
            });
        }
    }
    // z 순서를 별도로 보존한다. nodes/edges 분리는 표시 순서를 바꾸면 안 된다.
    return {
        schema_version: 1,
        engine: { name: "excalidraw", version: "0.18.1", adapter_version: 1 },
        settings: { background: "#F8F7F4", grid: "dots", width: 3200, height: 2100 },
        nodes,
        edges,
        element_order: elements.filter((e) => !e.isDeleted).map((e) => e.id),
    };
}
export function decode(document) {
    if (
        document.schema_version !== 1 ||
        document.engine.version !== "0.18.1" ||
        document.engine.adapter_version !== 1
    )
        throw new Error("문서 버전 불일치");
    const all = new Map(
        [...document.nodes, ...document.edges].map((item) => {
            const element = structuredClone(item.engine_element);
            if (item.type === "image")
                element.fileId = item.content.asset_id.replace(/^probe-asset-/, "");
            return [item.id, element];
        }),
    );
    return document.element_order.map((id) => all.get(id));
}
