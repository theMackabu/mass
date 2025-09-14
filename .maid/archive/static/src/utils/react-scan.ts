import { scan } from 'react-scan';
import { url } from '@/utils/search-params';
import { emitter } from '@/providers/emitter';

export function reactScan() {
  const enabled = url.get('scan') === 'true';

  emitter.on('react-scan', state => {
    state.enabled ? url.set('scan', 'true') : url.remove('scan');
    location.reload();
  });

  return scan({ enabled });
}
