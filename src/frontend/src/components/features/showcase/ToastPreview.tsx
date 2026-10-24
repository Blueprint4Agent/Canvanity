import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button, ToastCard } from "../../ui";
import type { ToastTone } from "../../ui/overlays/ToastCard";

type PreviewNotice = { id: number; tone: ToastTone; message: string };

export function ToastPreview({ showTones = false }: { showTones?: boolean }) {
    const { t } = useTranslation();
    const [notice, setNotice] = useState<PreviewNotice | null>(null);
    const show = (tone: ToastTone, message: string) => {
        setNotice((current) => ({ id: (current?.id ?? 0) + 1, tone, message }));
    };
    return (
        <>
            <Button onClick={() => show("success", t("showCase.toast.message"))}>
                {t("showCase.toast.trigger")}
            </Button>
            {showTones ? (
                <>
                    <Button onClick={() => show("error", t("toast.profileError"))}>
                        {t("showCase.toast.errorTrigger")}
                    </Button>
                    <Button onClick={() => show("neutral", t("showCase.catalog.localOnly"))}>
                        {t("showCase.toast.neutralTrigger")}
                    </Button>
                </>
            ) : null}
            {notice ? (
                <ToastCard
                    key={notice.id}
                    message={notice.message}
                    tone={notice.tone}
                    onDismiss={() => setNotice(null)}
                />
            ) : null}
        </>
    );
}
