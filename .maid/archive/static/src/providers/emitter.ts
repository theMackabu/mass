/* only ever create one emitter context */

import { createEmit } from '@/utils/emitter';

export type Events = {
  'react-scan': { enabled: boolean };
};

export const emitter = createEmit<Events>();
