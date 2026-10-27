import { ArrowUpRight, Lock, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { CommunityCanvas } from "../../components/features/explore/CommunityCanvas";
import { BoardCreateModal } from "../../components/features/board/BoardCreateModal";
import {
    Button,
    ButtonLink,
    InputField,
    InlineMessage,
    SegmentedControl,
    Spinner,
} from "../../components/ui";
import { useInterestCatalog } from "../../hooks/api/interests/useInterestCatalog";
import { useAuthContext } from "../../hooks/useAuth";
import { useBoardActions, useBoards } from "../../hooks/api/boards/useBoards";

export function BoardPage() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const { user, loading: authLoading } = useAuthContext();
    const [open, setOpen] = useState(false);
    const [input, setInput] = useState("");
    const [q, setQuery] = useState("");
    const [mine, setMine] = useState(false);
    const [cursors, setCursors] = useState<(string | undefined)[]>([undefined]);
    const boards = useBoards(q, mine && !!user, cursors[cursors.length - 1]);
    const actions = useBoardActions();
    const catalog = useInterestCatalog();
    useEffect(() => {
        setOpen(false);
        setMine(false);
        setCursors([undefined]);
    }, [user?.id]);
    const close = () => {
        setOpen(false);
        actions.clearError();
    };
    return (
        <>
            <CommunityCanvas
                label="Board"
                contentVersion={JSON.stringify([
                    "boards",
                    i18n.resolvedLanguage,
                    user?.id,
                    boards.data,
                    boards.error,
                    boards.loading,
                ])}
            >
                <header className="community-heading board-list-heading">
                    <h1>Board</h1>
                    <p className="explore-intro__tagline">{t("boards.subtitle")}</p>
                    <div className="board-heading-actions">
                        {user ? (
                            <Button
                                onClick={() => {
                                    actions.clearError();
                                    setOpen(true);
                                }}
                                disabled={!actions.available}
                            >
                                <Plus size={17} aria-hidden="true" />
                                {t("boards.create")}
                            </Button>
                        ) : (
                            <ButtonLink to="/login?next=%2Fboard">
                                {t("boards.loginToCreate")}
                            </ButtonLink>
                        )}
                    </div>
                </header>
                <section className="board-directory" aria-label={t("boards.directory")}>
                    <form
                        className="board-list-tools"
                        onSubmit={(event) => {
                            event.preventDefault();
                            setQuery(input.trim());
                            setCursors([undefined]);
                        }}
                    >
                        <InputField
                            label={t("boards.search")}
                            type="search"
                            value={input}
                            onValueChange={setInput}
                            maxLength={200}
                        />
                        <Button type="submit" disabled={!boards.available}>
                            {t("boards.searchAction")}
                        </Button>
                        {user ? (
                            <SegmentedControl
                                label={t("boards.filter")}
                                options={[
                                    { value: "all", label: t("boards.all") },
                                    { value: "mine", label: t("boards.mine") },
                                ]}
                                value={mine ? "mine" : "all"}
                                onChange={(value) => {
                                    setMine(value === "mine");
                                    setCursors([undefined]);
                                }}
                            />
                        ) : null}
                    </form>
                    {authLoading || boards.loading ? <Spinner label={t("boards.loading")} /> : null}
                    {boards.error ? (
                        <div className="board-feedback">
                            <InlineMessage tone="error">
                                {t(`boards.errors.${boards.error}`, {
                                    defaultValue: t("boards.errors.BOARD_UNAVAILABLE"),
                                })}
                            </InlineMessage>
                            <Button onClick={boards.reload}>{t("boards.retry")}</Button>
                        </div>
                    ) : null}
                    {!boards.available && !authLoading ? (
                        <InlineMessage>{t("boards.offline")}</InlineMessage>
                    ) : null}
                    {!boards.loading && !boards.error && boards.data?.items.length === 0 ? (
                        <div className="board-empty">
                            <h2>{t(q || mine ? "boards.noResults" : "boards.emptyTitle")}</h2>
                            <p>{t(q || mine ? "boards.noResultsHelp" : "boards.emptyHelp")}</p>
                        </div>
                    ) : null}
                    <div className="community-boards">
                        {boards.data?.items.map((board) => (
                            <Link
                                key={board.id}
                                to={`/b/${board.slug}`}
                                className="community-board board-live-card"
                            >
                                <div className="board-live-card__cover" aria-hidden="true">
                                    <span>{board.name.slice(0, 2)}</span>
                                </div>
                                <div className="community-board__caption">
                                    <h2>{board.name}</h2>
                                    <p>{board.description || t("boards.noDescription")}</p>
                                    <span>
                                        {board.visibility === "private" ? (
                                            <Lock size={14} aria-hidden="true" />
                                        ) : null}
                                        {t(`boards.${board.visibility}`)}
                                        <ArrowUpRight size={17} aria-hidden="true" />
                                    </span>
                                </div>
                            </Link>
                        ))}
                    </div>
                    <nav className="board-pagination" aria-label={t("boards.pagination")}>
                        {cursors.length > 1 ? (
                            <Button
                                appearance="canvas"
                                disabled={boards.loading}
                                onClick={() => setCursors((values) => values.slice(0, -1))}
                            >
                                {t("boards.previous")}
                            </Button>
                        ) : null}
                        {boards.data?.next_cursor ? (
                            <Button
                                appearance="canvas"
                                disabled={boards.loading}
                                onClick={() =>
                                    setCursors((values) => [...values, boards.data!.next_cursor!])
                                }
                            >
                                {t("boards.next")}
                            </Button>
                        ) : null}
                    </nav>
                </section>
            </CommunityCanvas>
            {open && user ? (
                <BoardCreateModal
                    catalog={catalog}
                    busy={actions.busy}
                    error={actions.error}
                    onClose={close}
                    onCreate={actions.create}
                    onCreated={(board) => {
                        close();
                        navigate(`/b/${board.slug}`);
                    }}
                />
            ) : null}
        </>
    );
}
