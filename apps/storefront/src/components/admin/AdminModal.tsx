"use client";

import { useEffect, useId, useRef, type MouseEvent, type ReactNode } from "react";

import { Icon } from "@/components/ui/Icon";

interface AdminModalProps {
  busy?: boolean;
  children: ReactNode;
  description?: string;
  onClose: () => void;
  open: boolean;
  title: string;
}

export function AdminModal({
  busy = false,
  children,
  description,
  onClose,
  open,
  title,
}: AdminModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  function requestClose() {
    if (!busy) onClose();
  }

  function closeFromBackdrop(event: MouseEvent<HTMLDialogElement>) {
    if (event.target === event.currentTarget) requestClose();
  }

  return (
    <dialog
      aria-labelledby={titleId}
      className="m-auto max-h-[calc(100dvh-2rem)] w-[min(48rem,calc(100vw-2rem))] overflow-hidden rounded-3xl border border-line bg-surface p-0 text-ink shadow-[0_30px_90px_rgba(19,35,31,0.28)] backdrop:bg-ink/60 backdrop:backdrop-blur-sm"
      onCancel={(event) => {
        event.preventDefault();
        requestClose();
      }}
      onClick={closeFromBackdrop}
      onClose={onClose}
      ref={dialogRef}
    >
      <div className="flex max-h-[calc(100dvh-2rem)] flex-col">
        <header className="flex shrink-0 items-start justify-between gap-5 border-b border-line bg-surface px-5 py-5 sm:px-7">
          <div>
            <h2 className="text-xl font-semibold" id={titleId}>{title}</h2>
            {description ? <p className="mt-1 text-sm leading-6 text-muted">{description}</p> : null}
          </div>
          <button
            aria-label="Đóng cửa sổ"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-muted transition hover:bg-paper hover:text-ink disabled:opacity-40"
            disabled={busy}
            onClick={requestClose}
            type="button"
          >
            <Icon name="close" size={19} />
          </button>
        </header>
        <div className="min-h-0 overflow-y-auto px-5 py-5 sm:px-7 sm:py-6">
          {children}
        </div>
      </div>
    </dialog>
  );
}
