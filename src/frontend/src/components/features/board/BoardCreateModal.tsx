import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import type { useInterestCatalog } from "../../../hooks/api/interests/useInterestCatalog";
import type { BoardCreateInput, BoardSummary } from "../../../hooks/api/boards/useBoards";
import { ProfileInterestsField } from "../profile/ProfileInterestsField";
import {
    Button,
    InputField,
    TextareaField,
    Modal,
    SegmentedControl,
    InlineMessage,
    Spinner,
} from "../../ui";

export function BoardCreateModal({
    busy,
    error,
    onClose,
    onCreate,
    onCreated,
    catalog,
}: {
    catalog: ReturnType<typeof useInterestCatalog>;
    busy: boolean;
    error: string | null;
    onClose: () => void;
    onCreate: (input: BoardCreateInput) => Promise<BoardSummary | undefined>;
    onCreated: (board: BoardSummary) => void;
}) {
    const { t } = useTranslation();
    const formId = useId();
    const [name, setName] = useState("");
    const [slug, setSlug] = useState("");
    const [description, setDescription] = useState("");
    const [interests, setInterests] = useState<string[]>([]);
    const [visibility, setVisibility] = useState<"public" | "private">("public");
    const close = () => {
        if (!busy) onClose();
    };
    return (
        <Modal
            open
            title={t("boards.createTitle")}
            description={t("boards.createDescription")}
            onClose={close}
            keyboardDismissible
            className="board-create-modal"
            footer={
                <>
                    <Button appearance="pill-secondary" onClick={close} disabled={busy}>
                        {t("boards.cancel")}
                    </Button>
                    <Button type="submit" form={formId} disabled={busy}>
                        {busy ? (
                            <Spinner size="sm" label={t("boards.creating")} />
                        ) : (
                            t("boards.create")
                        )}
                    </Button>
                </>
            }
        >
            <form
                id={formId}
                className="board-create-form"
                onSubmit={async (event) => {
                    event.preventDefault();
                    const board = await onCreate({
                        name: name.trim(),
                        slug: slug.trim(),
                        description: description.trim(),
                        interest_ids: interests,
                        visibility,
                        join_policy: visibility === "private" ? "invite" : "open",
                    });
                    if (board) onCreated(board);
                }}
            >
                <InputField
                    label={t("boards.name")}
                    value={name}
                    onValueChange={setName}
                    required
                    maxLength={80}
                    disabled={busy}
                    autoComplete="off"
                />
                <InputField
                    label={t("boards.address")}
                    value={slug}
                    onValueChange={setSlug}
                    required
                    minLength={3}
                    maxLength={64}
                    pattern="[a-z0-9]+(-[a-z0-9]+)*"
                    disabled={busy}
                    autoComplete="off"
                    autoCapitalize="none"
                    spellCheck={false}
                    aria-describedby={`${formId}-address`}
                    placeholder="my-board"
                />
                <p className="muted board-address-help" id={`${formId}-address`}>
                    <span>/b/{slug || "my-board"}</span> · {t("boards.addressHelp")}
                </p>
                <TextareaField
                    label={t("boards.description")}
                    value={description}
                    onValueChange={setDescription}
                    rows={3}
                    maxLength={2000}
                    disabled={busy}
                />
                <ProfileInterestsField
                    interests={interests}
                    onChange={setInterests}
                    busy={busy}
                    catalog={catalog}
                    maxSelections={3}
                    selectionHelp={t("boards.interestsHelp")}
                />
                <section className="board-visibility">
                    <h3>{t("boards.visibility")}</h3>
                    <SegmentedControl
                        label={t("boards.visibility")}
                        options={[
                            { value: "public", label: t("boards.public") },
                            { value: "private", label: t("boards.private") },
                        ]}
                        value={visibility}
                        onChange={(value) =>
                            setVisibility(value === "private" ? "private" : "public")
                        }
                        disabled={busy}
                    />
                    <p className="muted">
                        {t(visibility === "private" ? "boards.privateHelp" : "boards.publicHelp")}
                    </p>
                </section>
                <p className="muted">{t("boards.defaultsHelp")}</p>
                {error ? (
                    <InlineMessage tone="error">
                        {t(`boards.errors.${error}`, {
                            defaultValue: t("boards.errors.BOARD_UNAVAILABLE"),
                        })}
                    </InlineMessage>
                ) : null}
            </form>
        </Modal>
    );
}
