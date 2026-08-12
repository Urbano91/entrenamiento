import { useEffect, useRef } from 'react';

const activeModalIds: symbol[] = [];

export const useModalBehavior = (onClose: () => void, enabled = true) => {
    const modalId = useRef(Symbol('modal'));
    const onCloseRef = useRef(onClose);
    onCloseRef.current = onClose;

    useEffect(() => {
        if (!enabled) return;

        const id = modalId.current;
        const body = document.body;
        const previousOverflow = body.style.overflow;
        const previousPaddingRight = body.style.paddingRight;
        const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;

        activeModalIds.push(id);
        body.style.overflow = 'hidden';
        if (scrollbarWidth > 0) {
            const currentPaddingRight = Number.parseFloat(window.getComputedStyle(body).paddingRight) || 0;
            body.style.paddingRight = `${currentPaddingRight + scrollbarWidth}px`;
        }

        const handleKeyDown = (event: KeyboardEvent) => {
            const activeId = activeModalIds[activeModalIds.length - 1];
            if (event.key === 'Escape' && activeId === id) {
                event.preventDefault();
                onCloseRef.current();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            const index = activeModalIds.lastIndexOf(id);
            if (index >= 0) activeModalIds.splice(index, 1);
            body.style.overflow = previousOverflow;
            body.style.paddingRight = previousPaddingRight;
        };
    }, [enabled]);
};
