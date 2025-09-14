import { use, useRef, useState, useEffect, useCallback, createContext } from 'react';

interface ScrollState {
  scrollTop: number;
  isScrolledDown: boolean;
  isAtTop: boolean;
  isAtBottom: boolean;
}

interface ScrollContextValue {
  scrollRef: React.RefObject<HTMLDivElement | null>;
  scrollState: ScrollState;
  scrollTo: (options: ScrollToOptions) => void;
  scrollToTop: () => void;
  scrollToBottom: () => void;
}

interface ScrollProviderProps {
  className?: string;
  threshold?: number;
}

const ScrollContext = createContext<ScrollContextValue | null>(null);

export function ScrollProvider({
  children,
  className,
  threshold = 100,
}: Children<ScrollProviderProps>) {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const [scrollState, setScrollState] = useState<ScrollState>({
    scrollTop: 0,
    isScrolledDown: false,
    isAtTop: true,
    isAtBottom: false,
  });

  const updateScrollState = useCallback(() => {
    if (!scrollRef.current) return;

    const element = scrollRef.current;
    const scrollTop = element.scrollTop;
    const scrollHeight = element.scrollHeight;
    const clientHeight = element.clientHeight;

    setScrollState({
      scrollTop,
      isScrolledDown: scrollTop > threshold,
      isAtTop: scrollTop === 0,
      isAtBottom: scrollTop + clientHeight >= scrollHeight - 1,
    });
  }, [threshold]);

  const scrollTo = useCallback((options: ScrollToOptions) => {
    scrollRef.current?.scrollTo(options);
  }, []);

  const scrollToTop = useCallback(() => {
    scrollTo({ top: 0, behavior: 'smooth' });
  }, [scrollTo]);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [scrollTo]);

  useEffect(() => {
    const element = scrollRef.current;
    if (!element) return;

    const controller = new AbortController();

    element.addEventListener('scroll', updateScrollState, {
      passive: true,
      signal: controller.signal,
    });

    updateScrollState();

    return () => controller.abort();
  }, [updateScrollState]);

  const contextValue: ScrollContextValue = {
    scrollRef,
    scrollState,
    scrollTo,
    scrollToTop,
    scrollToBottom,
  };

  return (
    <ScrollContext.Provider value={contextValue}>
      <div ref={scrollRef} className={className}>
        {children}
      </div>
    </ScrollContext.Provider>
  );
}

export function useScroll(): ScrollContextValue {
  const context = use(ScrollContext);

  if (!context) {
    throw new Error('useScroll must be used within a ScrollProvider');
  }

  return context;
}
