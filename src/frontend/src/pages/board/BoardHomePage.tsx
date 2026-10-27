import { ArrowLeft, Lock, Megaphone, MessagesSquare } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router-dom";
import { CommunityCanvas } from "../../components/features/explore/CommunityCanvas";
import { ProfileInterestTags } from "../../components/features/profile/ProfileInterestsField";
import { Button, ButtonLink, InlineMessage, InputField, Modal, Spinner } from "../../components/ui";
import { useBoardActions, useBoardHome } from "../../hooks/api/boards/useBoards";
import { useInterestCatalog } from "../../hooks/api/interests/useInterestCatalog";

export function BoardHomePage() {
    const { slug = "" } = useParams();
    const { t, i18n } = useTranslation();
    const home = useBoardHome(slug);
    const catalog = useInterestCatalog();
    const actions = useBoardActions();
    const navigate = useNavigate();
    const [deleting, setDeleting] = useState(false);
    const [confirmation, setConfirmation] = useState("");
    const data = home.data;
    useEffect(() => {
        setDeleting(false);
        setConfirmation("");
    }, [slug]);
    return (
        <>
            <CommunityCanvas
                label={data?.board.name ?? "Board"}
                contentVersion={JSON.stringify([
                    "board-home",
                    slug,
                    i18n.resolvedLanguage,
                    data,
                    catalog.items,
                    home.error,
                    home.loading,
                ])}
            >
                <header className="community-heading board-home-heading">
                    <ButtonLink to="/board" appearance="canvas">
                        <ArrowLeft size={15} aria-hidden="true" />
                        {t("boards.back")}
                    </ButtonLink>
                    <h1>{data?.board.name ?? "Board"}</h1>
                    <p className="explore-intro__tagline">A place to pin, share, and belong.</p>
                </header>
                {home.loading ? <Spinner label={t("boards.loading")} /> : null}
                {home.error ? (
                    <div className="board-feedback">
                        <InlineMessage tone="error">
                            {t(`boards.errors.${home.error}`, {
                                defaultValue: t("boards.errors.BOARD_UNAVAILABLE"),
                            })}
                        </InlineMessage>
                        <Button onClick={home.reload}>{t("boards.retry")}</Button>
                    </div>
                ) : null}
                {!home.available && !home.loading ? (
                    <InlineMessage>{t("boards.offline")}</InlineMessage>
                ) : null}
                {data ? (
                    <div className="board-home-content">
                        <section className="board-home-intro" aria-label={t("boards.about")}>
                            <p className="board-visibility-label">
                                {data.board.visibility === "private" ? (
                                    <Lock size={15} aria-hidden="true" />
                                ) : null}
                                {t(`boards.${data.board.visibility}`)}
                            </p>
                            <p className="board-description">
                                {data.board.description || t("boards.noDescription")}
                            </p>
                            <div className="profile-interests">
                                <ProfileInterestTags
                                    interests={data.board.interest_ids}
                                    catalog={catalog.items}
                                />
                            </div>
                            {data.membership ? (
                                <p className="muted">
                                    {t(
                                        data.membership.role === "owner"
                                            ? "boards.owner"
                                            : "boards.member",
                                    )}{" "}
                                    · {data.membership.grade_name}
                                </p>
                            ) : null}
                            {data.rules ? <p className="board-rules">{data.rules}</p> : null}
                        </section>
                        <section className="board-home-shelves" aria-label={t("boards.shelves")}>
                            <h2>{t("boards.shelves")}</h2>
                            {data.shelves.map((shelf) => (
                                <div key={shelf.id} className="board-shelf-row">
                                    {shelf.purpose === "notice" ? (
                                        <Megaphone size={20} aria-hidden="true" />
                                    ) : (
                                        <MessagesSquare size={20} aria-hidden="true" />
                                    )}
                                    <div>
                                        <h3>{shelf.name}</h3>
                                        <p>
                                            {shelf.description ||
                                                t(
                                                    shelf.purpose === "notice"
                                                        ? "boards.noticeHelp"
                                                        : "boards.generalHelp",
                                                )}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </section>
                        <section className="board-home-latest" aria-label={t("boards.latest")}>
                            <h2>{t("boards.latest")}</h2>
                            <div className="board-empty">
                                <h3>{t("boards.noCanvas")}</h3>
                                <p>{t("boards.noCanvasHelp")}</p>
                            </div>
                        </section>
                        {data.membership?.role === "owner" ? (
                            <div className="board-owner-actions">
                                <Button
                                    appearance="canvas"
                                    onClick={() => {
                                        setConfirmation("");
                                        actions.clearError();
                                        setDeleting(true);
                                    }}
                                >
                                    {t("boards.deleteEmpty")}
                                </Button>
                            </div>
                        ) : null}
                    </div>
                ) : null}
            </CommunityCanvas>
            {deleting && data && data.membership?.role === "owner" ? (
                <Modal
                    open
                    keyboardDismissible
                    title={t("boards.deleteTitle")}
                    description={t("boards.deleteHelp")}
                    onClose={() => {
                        if (!actions.busy) setDeleting(false);
                    }}
                    footer={
                        <>
                            <Button
                                appearance="pill-secondary"
                                disabled={actions.busy}
                                onClick={() => setDeleting(false)}
                            >
                                {t("boards.cancel")}
                            </Button>
                            <Button
                                disabled={actions.busy || confirmation !== data.board.slug}
                                onClick={async () => {
                                    if (await actions.remove(data.board, confirmation))
                                        navigate("/board");
                                }}
                            >
                                {t("boards.deleteConfirm")}
                            </Button>
                        </>
                    }
                >
                    <InputField
                        label={t("boards.deleteAddress", { slug: data.board.slug })}
                        value={confirmation}
                        onValueChange={setConfirmation}
                        disabled={actions.busy}
                        autoComplete="off"
                    />
                    {actions.error ? (
                        <InlineMessage tone="error">
                            {t(`boards.errors.${actions.error}`, {
                                defaultValue: t("boards.errors.BOARD_UNAVAILABLE"),
                            })}
                        </InlineMessage>
                    ) : null}
                </Modal>
            ) : null}
        </>
    );
}
