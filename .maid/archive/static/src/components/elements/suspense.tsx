import { Suspense } from 'react';
import { useRef, useEffect } from 'react';

export function SuspenseWithPrevious({ children, ...props }: Children) {
  const previousChildrenRef = useRef(children);

  useEffect(() => {
    previousChildrenRef.current = children;
  }, [children]);

  return (
    <Suspense fallback={previousChildrenRef.current} {...props}>
      {children}
    </Suspense>
  );
}
