import { validateSurface } from "../../../canvas/canvasRules";
export const EXPLORE_SURFACE = validateSurface({
    kind: "ui",
    bounds: { width: 2400, height: 1600 },
});
export const WORLD = EXPLORE_SURFACE.bounds;
export type ExploreTopicId = "agent" | "build" | "daily" | "learn" | "play" | "ideas";
export type ExploreTopic = {
    id: ExploreTopicId;
    x: number;
    y: number;
    preview: "flow" | "code" | "photo" | "notes" | "game" | "ideas";
};
const TOPICS: readonly ExploreTopic[] = [
    { id: "agent", x: 100, y: 380, preview: "flow" },
    { id: "build", x: 160, y: 650, preview: "code" },
    { id: "daily", x: 480, y: 205, preview: "photo" },
    { id: "learn", x: 670, y: 650, preview: "notes" },
    { id: "play", x: 1100, y: 600, preview: "game" },
    { id: "ideas", x: 900, y: 140, preview: "ideas" },
];
export const EXPLORE_ORIGIN = { x: 480, y: 300 };
export const EXPLORE_OVERVIEW = { x: 480, y: 300, width: 1440, height: 1000 };
export const INTRO_RECT = { x: 580, y: 435, width: 350, height: 170 };

export const EXPLORE_TOPICS: readonly ExploreTopic[] = TOPICS.map((topic) => ({
    ...topic,
    x: topic.x + EXPLORE_ORIGIN.x,
    y: topic.y + EXPLORE_ORIGIN.y,
}));
