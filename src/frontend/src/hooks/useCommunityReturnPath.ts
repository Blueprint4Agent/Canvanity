import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { storageKey } from "../utils/basePath";

const SPACES = new Set(["/home", "/my-canvas", "/board"]);
const KEY = storageKey("canvanity_last_community_path");
function readLastPath() {
    try {
        const path = sessionStorage.getItem(KEY);
        return path && SPACES.has(path.split("?")[0]) ? path : "/home";
    } catch {
        return "/home";
    }
}
export function useCommunityReturnPath() {
    const { pathname, search } = useLocation();
    const [lastPath, setLastPath] = useState(readLastPath);
    const current = SPACES.has(pathname) ? pathname + search : null;
    useEffect(() => {
        if (!current) return;
        setLastPath(current);
        try {
            sessionStorage.setItem(KEY, current);
        } catch {
            /* Browsing still works without storage. */
        }
    }, [current]);
    return current ?? lastPath;
}
