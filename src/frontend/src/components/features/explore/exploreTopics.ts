import { validateSurface } from "../../../canvas/canvasRules";
export const EXPLORE_SURFACE = validateSurface({
    kind: "ui",
    bounds: { width: 3200, height: 2100 },
});
export const WORLD = EXPLORE_SURFACE.bounds;
export type ExploreTopicId = "agent" | "build" | "daily" | "learn";
export type ExploreImageId = ExploreTopicId | "play" | "ideas";
export type ExplorePost = {
    id: string;
    image: ExploreImageId;
    author: "seoyeon" | "minjae" | "doyun" | "haneul" | "jiwon" | "jimin" | "yuna" | "jun";
    likes: number;
    comments?: number;
};
export type ExploreTopic = {
    id: ExploreTopicId;
    x: number;
    y: number;
    posts: readonly ExplorePost[];
};
// Stable, intentionally scattered coordinates preserve spatial memory across visits.
export const EXPLORE_TOPICS: readonly ExploreTopic[] = [
    {
        id: "daily",
        x: 440,
        y: 500,
        posts: [{ id: "light", image: "daily", author: "seoyeon", likes: 428, comments: 32 }],
    },
    {
        id: "learn",
        x: 1530,
        y: 390,
        posts: [
            { id: "quiet", image: "build", author: "minjae", likes: 312, comments: 18 },
            { id: "escape", image: "ideas", author: "doyun", likes: 367, comments: 24 },
        ],
    },
    {
        id: "build",
        x: 1420,
        y: 1030,
        posts: [
            { id: "routine", image: "play", author: "haneul", likes: 198, comments: 16 },
            { id: "workspace", image: "agent", author: "jiwon", likes: 519, comments: 41 },
        ],
    },
    {
        id: "agent",
        x: 530,
        y: 1080,
        posts: [
            { id: "days", image: "agent", author: "yuna", likes: 124, comments: 12 },
            { id: "collected", image: "daily", author: "jun", likes: 93, comments: 8 },
        ],
    },
];
export const EXPLORE_OVERVIEW = { x: 340, y: 160, width: 2180, height: 1370 };
export const INTRO_RECT = { x: 460, y: 220, width: 700, height: 180 };
