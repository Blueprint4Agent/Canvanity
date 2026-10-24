import { useCallback, useEffect, useMemo, useState } from "react";
import { Hand, MousePointer2, Plus, Minus, Scan, X, ArrowLeft, ArrowUpRight } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button, InputField, Tooltip, KeyboardShortcut, BrandMark } from "../../ui";
import { ExploreCluster } from "./ExploreCluster";
import {
    EXPLORE_TOPICS,
    EXPLORE_OVERVIEW,
    EXPLORE_SURFACE,
    INTRO_RECT,
    type ExploreTopicId,
} from "./exploreTopics";
import { useCanvasSnapshot } from "../../../hooks/useCanvasSnapshot";
import { useCanvasCamera } from "../../../hooks/useCanvasCamera";

import { CANVAS_RULES, CANVAS_SHORTCUTS, CANVAS_PAN_KEY } from "../../../canvas/canvasRules";
import { useCanvasPanMode } from "../../../hooks/useCanvasPanMode";

import { useCanvasShortcuts } from "../../../hooks/useCanvasShortcuts";

export function ExploreCanvas() {
    const { t, i18n } = useTranslation();
    const spaceHeld = useCanvasPanMode();
    const camera = useCanvasCamera(EXPLORE_SURFACE, INTRO_RECT, EXPLORE_OVERVIEW, spaceHeld);
    const snapshot = useCanvasSnapshot(
        camera.worldRef,
        EXPLORE_SURFACE,
        `${i18n.resolvedLanguage ?? "ko"}:discovery-feed-v1`,
    );
    const [searchParams, setSearchParams] = useSearchParams();
    const [selected, setSelected] = useState<ExploreTopicId | null>(null);
    const [searchOpen, setSearchOpen] = useState(false);
    const [query, setQuery] = useState("");
    const tool = spaceHeld ? "hand" : "select";
    const focusRect = camera.focus;
    const searchRequested = searchParams.get("search") === "1";
    useEffect(() => {
        if (searchRequested) setSearchOpen(true);
    }, [searchRequested]);
    const closeSearch = useCallback(() => {
        setSearchOpen(false);
        setSearchParams(
            (params) => {
                params.delete("search");
                return params;
            },
            { replace: true },
        );
    }, [setSearchParams]);

    const selectTopic = useCallback(
        (id: ExploreTopicId) => {
            const topic = EXPLORE_TOPICS.find((item) => item.id === id)!;
            setSelected(id);
            closeSearch();
            const node = camera.worldRef.current?.querySelector<HTMLElement>(
                `.explore-cluster--${id}`,
            );
            focusRect({
                x: topic.x - 32,
                y: topic.y - 32,
                width: (node?.offsetWidth ?? 310) + 64,
                height: (node?.offsetHeight ?? 240) + 64,
            });
        },
        [focusRect, closeSearch, camera.worldRef],
    );
    const reset = () => {
        setSelected(null);
        camera.fit();
    };
    const zoomAt = camera.zoomAt;
    const fitAll = camera.fit;
    const actions = useMemo(
        () => ({
            select: () => camera.viewportRef.current?.focus({ preventScroll: true }),
            search: () => setSearchOpen(true),
            zoomIn: () => zoomAt(CANVAS_RULES.zoomStep),
            zoomOut: () => zoomAt(1 / CANVAS_RULES.zoomStep),
            fit: () => {
                setSelected(null);
                fitAll();
            },
        }),
        [zoomAt, fitAll],
    );
    useCanvasShortcuts(camera.viewportRef, actions);
    const searchResults = EXPLORE_TOPICS.filter((topic) =>
        t(`explore.topics.${topic.id}.label`)
            .toLocaleLowerCase()
            .includes(query.trim().toLocaleLowerCase()),
    );
    return (
        <div className="explore-page" data-tool={tool}>
            {searchOpen ? (
                <section className="explore-search" aria-label={t("explore.search")}>
                    <InputField
                        type="search"
                        autoFocus
                        label={t("explore.searchLabel")}
                        placeholder={t("explore.searchPlaceholder")}
                        value={query}
                        onValueChange={setQuery}
                        onKeyDown={(event) => {
                            if (event.key === "Escape") closeSearch();
                            if (event.key === "Enter" && searchResults[0])
                                selectTopic(searchResults[0].id);
                        }}
                    />
                    <div className="explore-search__results">
                        {searchResults.map((topic) => (
                            <Button
                                key={topic.id}
                                appearance="text"
                                onClick={() => selectTopic(topic.id)}
                            >
                                {t(`explore.topics.${topic.id}.label`)}
                                <ArrowUpRight size={14} />
                            </Button>
                        ))}
                        {!searchResults.length ? <p>{t("explore.noResults")}</p> : null}
                    </div>
                    <Button
                        appearance="text"
                        iconOnly
                        aria-label={t("explore.closeSearch")}
                        onClick={() => closeSearch()}
                    >
                        <X size={16} />
                    </Button>
                </section>
            ) : null}
            <div
                role="region"
                ref={camera.viewportRef}
                className="explore-viewport"
                tabIndex={0}
                aria-label={t("explore.canvasLabel")}
                data-dragging={camera.dragging}
                onClickCapture={camera.onClickCapture}
                onDragStart={(event) => event.preventDefault()}
                onPointerDown={camera.onPointerDown}
                onPointerMove={camera.onPointerMove}
                onPointerUp={camera.onPointerUp}
                onPointerCancel={camera.onPointerUp}
                onLostPointerCapture={camera.onPointerUp}
                onKeyDown={(event) => {
                    if (!["+", "=", "-", "0"].includes(event.key)) camera.onKeyDown(event);
                    if (event.key === "Escape") setSelected(null);
                }}
            >
                <div ref={camera.worldRef} className="explore-world">
                    <div className="explore-content">
                        <section className="explore-intro" aria-labelledby="home-project-title">
                            <h1 id="home-project-title">
                                <BrandMark />
                                <span>{t("nav.brand")}</span>
                            </h1>
                            <p className="explore-intro__tagline">{t("explore.tagline")}</p>
                        </section>
                        {EXPLORE_TOPICS.map((topic) => (
                            <ExploreCluster
                                key={topic.id}
                                topic={topic}
                                active={selected === topic.id}
                                onSelect={selectTopic}
                            />
                        ))}
                    </div>
                </div>
            </div>
            <nav className="explore-tools" aria-label={t("explore.tools")}>
                <Tooltip
                    content={
                        <span className="ui-shortcut-hint">
                            {t("explore.select")}
                            <KeyboardShortcut keys={[CANVAS_SHORTCUTS.select.toUpperCase()]} />
                        </span>
                    }
                    side="right"
                >
                    <Button
                        appearance="text"
                        iconOnly
                        aria-label={t("explore.select")}
                        aria-pressed={tool === "select"}
                        onClick={() => camera.viewportRef.current?.focus({ preventScroll: true })}
                    >
                        <MousePointer2 size={20} />
                    </Button>
                </Tooltip>
                <Tooltip
                    content={
                        <span className="ui-shortcut-hint">
                            {t("explore.panHold")}
                            <KeyboardShortcut keys={[CANVAS_PAN_KEY]} />
                        </span>
                    }
                    side="right"
                >
                    <span
                        className="explore-pan-hint"
                        tabIndex={0}
                        role="img"
                        aria-label={t("explore.panHold")}
                        data-active={spaceHeld}
                    >
                        <Hand size={20} />
                    </span>
                </Tooltip>
            </nav>
            {selected ? (
                <aside className="explore-selection" aria-live="polite">
                    <Button
                        appearance="text"
                        iconOnly
                        aria-label={t("explore.back")}
                        onClick={() => {
                            setSelected(null);
                            focusRect(INTRO_RECT);
                        }}
                    >
                        <ArrowLeft size={17} />
                    </Button>
                    <span>
                        <strong>{t(`explore.topics.${selected}.label`)}</strong>
                        <span>{t(`explore.topics.${selected}.description`)}</span>
                    </span>
                </aside>
            ) : null}
            <div className="explore-map">
                <div className="explore-zoom-tools">
                    <span className="explore-zoom" aria-label={t("explore.zoomLevel")}>
                        {Math.round(camera.zoom * 100)}%
                    </span>
                    <Tooltip
                        content={
                            <span className="ui-shortcut-hint">
                                {t("explore.zoomIn")}
                                <KeyboardShortcut keys={["mod", CANVAS_SHORTCUTS.zoomIn]} />
                            </span>
                        }
                        side="right"
                    >
                        <Button
                            appearance="text"
                            iconOnly
                            aria-label={t("explore.zoomIn")}
                            disabled={camera.zoom >= CANVAS_RULES.maxZoom}
                            aria-keyshortcuts="+"
                            onClick={() => camera.zoomAt(CANVAS_RULES.zoomStep)}
                        >
                            <Plus size={20} />
                        </Button>
                    </Tooltip>
                    <Tooltip
                        content={
                            <span className="ui-shortcut-hint">
                                {t("explore.zoomOut")}
                                <KeyboardShortcut keys={["mod", CANVAS_SHORTCUTS.zoomOut]} />
                            </span>
                        }
                        side="right"
                    >
                        <Button
                            appearance="text"
                            iconOnly
                            aria-label={t("explore.zoomOut")}
                            disabled={camera.zoom <= CANVAS_RULES.minZoom}
                            aria-keyshortcuts="-"
                            onClick={() => camera.zoomAt(1 / CANVAS_RULES.zoomStep)}
                        >
                            <Minus size={20} />
                        </Button>
                    </Tooltip>
                    <Tooltip
                        content={
                            <span className="ui-shortcut-hint">
                                {t("explore.fit")}
                                <KeyboardShortcut keys={["mod", CANVAS_SHORTCUTS.fit]} />
                            </span>
                        }
                        side="right"
                    >
                        <Button
                            appearance="text"
                            iconOnly
                            aria-label={t("explore.fit")}
                            aria-keyshortcuts="0"
                            onClick={reset}
                        >
                            <Scan size={20} />
                        </Button>
                    </Tooltip>
                </div>
                <Button
                    appearance="text"
                    className="explore-minimap"
                    aria-label={t("explore.mapNavigate")}
                    onClick={camera.onMapClick}
                    onPointerDown={camera.onMapPointerDown}
                    onPointerMove={camera.onMapPointerMove}
                    onPointerUp={camera.onMapPointerUp}
                    onPointerCancel={camera.onMapPointerUp}
                    onLostPointerCapture={camera.onMapPointerUp}
                    disabled={!snapshot.image}
                    aria-busy={snapshot.loading}
                >
                    <span className="explore-minimap__canvas" aria-hidden="true">
                        {snapshot.image ? (
                            <img src={snapshot.image} alt="" draggable={false} />
                        ) : (
                            <span className="explore-snapshot-status">
                                {t(
                                    snapshot.failed
                                        ? "explore.snapshotError"
                                        : "explore.snapshotLoading",
                                )}
                            </span>
                        )}
                        <span ref={camera.mapWindowRef} className="explore-minimap__viewport" />
                    </span>
                </Button>
                {snapshot.failed ? (
                    <Button appearance="text" onClick={snapshot.refresh}>
                        {t("explore.retrySnapshot")}
                    </Button>
                ) : null}
            </div>
        </div>
    );
}
