import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useAuthContext } from "../../useAuth";
import { useToast } from "../../useToast";
import { useAuthApi } from "./useAuthApi";

export function useProfileEditor() {
    const { user, updateProfile, uploadPhoto, deletePhoto } = useAuthContext();
    const { extractApiDetail, resolveAuthErrorMessage } = useAuthApi();
    const { t } = useTranslation();
    const toast = useToast();
    const [open, setOpen] = useState(false);
    const [editing, setEditing] = useState<"name" | "bio" | "location" | "handle" | null>(null);
    const [name, setName] = useState("");
    const [bio, setBio] = useState("");
    const [handle, setHandle] = useState("");
    const [interests, setInterests] = useState<string[]>([]);
    const [interestsOpen, setInterestsOpen] = useState(false);
    const handleValid = !handle.trim() || /^[a-z0-9가-힣_]{2,24}$/.test(handle.trim());
    const interestsValid = interests.length <= 8;
    const [location, setLocation] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const epoch = useRef(0);
    const pending = useRef(false);
    useEffect(() => {
        ++epoch.current;
        setOpen(false);
        setEditing(null);
        setName("");
        setBio("");
        setHandle("");
        setInterests([]);
        setInterestsOpen(false);
        setLocation("");
        setError("");
        setBusy(false);
        pending.current = false;
        return () => {
            ++epoch.current;
        };
    }, [user?.id]);
    useEffect(() => {
        if (!editing) return;
        const cancelOnEscape = (event: KeyboardEvent) => {
            if (event.key !== "Escape" || event.defaultPrevented || pending.current) return;
            event.preventDefault();
            setEditing(null);
            setError("");
        };
        window.addEventListener("keydown", cancelOnEscape);
        return () => window.removeEventListener("keydown", cancelOnEscape);
    }, [editing]);
    const perform = async (action: () => Promise<void>, close = false) => {
        if (pending.current || !user) return;
        const current = epoch.current;
        pending.current = true;
        setBusy(true);
        setError("");
        try {
            await action();
            if (current !== epoch.current) return;
            toast(t("toast.profileSuccess"), { tone: "success" });
            if (close) {
                setOpen(false);
                setInterestsOpen(false);
                setEditing(null);
            }
        } catch (failure) {
            if (current === epoch.current)
                setError(
                    resolveAuthErrorMessage(t, extractApiDetail(failure), "toast.profileError"),
                );
        } finally {
            if (current === epoch.current) {
                pending.current = false;
                setBusy(false);
            }
        }
    };
    return {
        open,
        editing,
        startInline: (field: "name" | "bio" | "location" | "handle") => {
            if (pending.current) return;
            setName(user?.name ?? "");
            setBio(user?.bio ?? "");
            setHandle(user?.handle ?? "");
            setInterests(user?.interests ?? []);
            setLocation(user?.location ?? "");
            setError("");
            setEditing(field);
        },
        cancelInline: () => {
            if (!pending.current) {
                setEditing(null);
                setError("");
            }
        },
        saveInline: () => {
            if (
                !editing ||
                (editing === "name" && name.trim().length < 2) ||
                (editing === "handle" && !handleValid)
            )
                return;
            const value =
                editing === "name"
                    ? name.trim()
                    : editing === "bio"
                      ? bio.trim() || null
                      : editing === "handle"
                        ? handle.trim() || null
                        : location || null;
            void perform(() => updateProfile({ [editing]: value }), true);
        },
        name,
        bio,
        handle,
        interests,
        handleValid,
        interestsValid,
        setHandle: (value: string) => setHandle(value.replace(/^@/, "").toLowerCase()),
        setInterests,
        interestsOpen,
        location,
        busy,
        error,
        setName,
        setBio: (value: string) => setBio(Array.from(value).slice(0, 100).join("")),
        setLocation,
        show: () => {
            setEditing(null);
            setName(user?.name ?? "");
            setBio(user?.bio ?? "");
            setHandle(user?.handle ?? "");
            setInterests(user?.interests ?? []);
            setLocation(user?.location ?? "");
            setError("");
            setOpen(true);
        },
        close: () => {
            if (!pending.current) {
                setOpen(false);
                setError("");
            }
        },
        save: () => {
            if (name.trim().length >= 2 && handleValid && interestsValid)
                void perform(
                    () =>
                        updateProfile({
                            name: name.trim(),
                            bio: bio.trim() || null,
                            handle: handle.trim() || null,
                            interests,
                            location: location.trim() || null,
                        }),
                    true,
                );
        },
        showInterests: () => {
            if (pending.current) return;
            setEditing(null);
            setInterests(user?.interests ?? []);
            setError("");
            setInterestsOpen(true);
        },
        closeInterests: () => {
            if (!pending.current) {
                setInterestsOpen(false);
                setError("");
            }
        },
        saveInterests: () => {
            if (interestsValid) void perform(() => updateProfile({ interests }), true);
        },
        removeInterest: (interest: string) => {
            if (!pending.current)
                void perform(() =>
                    updateProfile({
                        interests: (user?.interests ?? []).filter((value) => value !== interest),
                    }),
                );
        },
        removePhoto: () => void perform(deletePhoto),
        selectPhoto: (file: File) => {
            if (pending.current) return;
            if (
                !["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"].includes(
                    file.type,
                )
            ) {
                setError(t("settings.profile.photoTypeError"));
                return;
            }
            if (file.size > 8 * 1024 * 1024) {
                setError(t("settings.profile.photoSizeError"));
                return;
            }
            void perform(() => uploadPhoto(file));
        },
    };
}
