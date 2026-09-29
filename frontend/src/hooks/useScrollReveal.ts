import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Enterprise Scroll-Reveal Hook for SIH26108 BIS SpecEngine.
 * Observes elements with `data-reveal` or `.scroll-reveal` and smoothly reveals
 * them as they enter the viewport. Once revealed, elements stay visible permanently.
 * Respects prefers-reduced-motion and gracefully falls back if IntersectionObserver is absent.
 */
export function useScrollReveal() {
  const location = useLocation();

  useEffect(() => {
    // Check if user prefers reduced motion
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Elements to reveal
    const getElements = () =>
      document.querySelectorAll<HTMLElement>('[data-reveal], .scroll-reveal');

    if (prefersReducedMotion || typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      // Immediate reveal without motion
      getElements().forEach((el) => {
        el.classList.add('is-revealed');
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const target = entry.target as HTMLElement;
            target.classList.add('is-revealed');
            observer.unobserve(target);
          }
        });
      },
      {
        rootMargin: '0px 0px -40px 0px',
        threshold: 0.05,
      }
    );

    // Initial query on mount / route change
    const elements = getElements();
    elements.forEach((el) => {
      // If already revealed, do not re-observe
      if (!el.classList.contains('is-revealed')) {
        observer.observe(el);
      }
    });

    // Also watch for dynamically injected elements (e.g. async results) via MutationObserver
    let mutationObserver: MutationObserver | null = null;
    if ('MutationObserver' in window) {
      mutationObserver = new MutationObserver(() => {
        const newElements = getElements();
        newElements.forEach((el) => {
          if (!el.classList.contains('is-revealed')) {
            observer.observe(el);
          }
        });
      });

      mutationObserver.observe(document.body, {
        childList: true,
        subtree: true,
      });
    }

    return () => {
      observer.disconnect();
      if (mutationObserver) {
        mutationObserver.disconnect();
      }
    };
  }, [location.pathname]);
}
