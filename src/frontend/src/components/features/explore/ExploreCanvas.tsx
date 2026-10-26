import { CanvasControls } from "./CanvasControls";
import { useCallback, useEffect, useMemo, useState } from "react";
import { X, ArrowLeft, ArrowUpRight } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button, InputField } from "../../ui";
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

import { CANVAS_RULES } from "../../../canvas/canvasRules";
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
    const requestedTopic = searchParams.get("topic");
    useEffect(() => {
        if (EXPLORE_TOPICS.some((topic) => topic.id === requestedTopic)) {
            selectTopic(requestedTopic as ExploreTopicId);
        }
    }, [requestedTopic, selectTopic]);
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
                                appearance="canvas"
                                onClick={() => selectTopic(topic.id)}
                            >
                                {t(`explore.topics.${topic.id}.label`)}
                                <ArrowUpRight size={14} />
                            </Button>
                        ))}
                        {!searchResults.length ? <p>{t("explore.noResults")}</p> : null}
                    </div>
                    <Button
                        appearance="canvas"
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
                            <h1 id="home-project-title">Plaza</h1>
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
            {selected ? (
                <aside className="explore-selection" aria-live="polite">
                    <Button
                        appearance="canvas"
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

            <CanvasControls
                camera={camera}
                snapshot={snapshot}
                spaceHeld={spaceHeld}
                onReset={reset}
            />
        </div>
    );
}
