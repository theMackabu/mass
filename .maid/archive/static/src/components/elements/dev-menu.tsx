// import { useEffect } from 'react';
import { url } from '@/utils/search-params';
import { emitter } from '@/providers/emitter';
import { useModel } from '@furry/model';

import { X } from 'lucide-react';
import { Fragment } from 'react';

export function DevMenu() {
  if (import.meta.env.PROD) return null;
  return <DevTools />;
}

export function DevTools() {
  const pfmEnabled = url.get('scan') === 'true';

  const [state, event] = useModel({
    visible: url.get('devtools') === 'true',
  });

  const toggleDevTools = () => {
    event.visible.set(!state.visible);
    url.set('devtools', !state.visible ? 'true' : 'false');
  };

  // useEffect(() => {
  //
  // }, []);

  return (
    <div className="select-none fixed bottom-4 left-4 z-50 hidden md:block">
      <button
        type="button"
        onClick={toggleDevTools}
        className="group flex items-center gap-2 p-1 bg-black/90 hover:bg-black/95 dark:bg-white/10 dark:hover:bg-white/20 backdrop-blur-sm text-white dark:text-white font-medium rounded-full border border-white/10 shadow-lg shadow-black/20 transition-all duration-200 ease-in-out hover:scale-102 active:scale-95 cursor-pointer"
      >
        {state.visible ? (
          <X className="size-3" />
        ) : (
          <span className="px-2 py-1 text-xs">Show DevTools</span>
        )}
      </button>

      {state.visible && (
        <Fragment>
          <div className="mt-1.5 w-60 h-60 p-2 bg-black/90 dark:bg-white/10 backdrop-blur-sm text-white dark:text-white text-xs font-medium rounded-lg border border-white/10 shadow-lg overflow-scroll">
            <pre>visible: {state.visible ? 'true' : 'false'}</pre>
          </div>

          <div className="flex gap-x-1 justify-center">
            <button
              type="button"
              onClick={() => location.reload()}
              className="group flex items-center mt-1.5 gap-2 px-3 py-2 bg-black/90 hover:bg-black/95 dark:bg-white/10 dark:hover:bg-white/20 backdrop-blur-sm text-white dark:text-white text-xs font-medium rounded-full border border-white/10 shadow-lg shadow-black/20 transition-all duration-200 ease-in-out hover:scale-102 active:scale-95 cursor-pointer"
            >
              <span className="whitespace-nowrap">Reload Page</span>
            </button>

            <button
              type="button"
              onClick={() => emitter.emit('react-scan', { enabled: pfmEnabled ? false : true })}
              className="group flex items-center mt-1.5 gap-2 px-3 py-2 bg-black/90 hover:bg-black/95 dark:bg-white/10 dark:hover:bg-white/20 backdrop-blur-sm text-white dark:text-white text-xs font-medium rounded-full border border-white/10 shadow-lg shadow-black/20 transition-all duration-200 ease-in-out hover:scale-102 active:scale-95 cursor-pointer"
            >
              <span className="whitespace-nowrap">
                {pfmEnabled ? 'Disable' : 'Enable'} Perf Monitor
              </span>
            </button>
          </div>
        </Fragment>
      )}
    </div>
  );
}
