import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { storageKey } from "../utils/basePath";

const SPACES = new Set(["/home", "/my-canvas", "/board"]);
function isCommunityPath(path: string) {
    const pathname = path.split("?")[0];
    return SPACES.has(pathname) || /^\/b\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(pathname);
}
const KEY = storageKey("canvanity_last_community_path");
function readLastPath() {
    try {
        const path = sessionStorage.getItem(KEY);
        return path && isCommunityPath(path) ? path : "/home";
    } catch {
        return "/home";
    }
}
export function useCommunityReturnPath() {
    const { pathname, search } = useLocation();
    const [lastPath, setLastPath] = useState(readLastPath);
    const current = isCommunityPath(pathname) ? pathname + search : null;
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
