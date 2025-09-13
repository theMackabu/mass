import server from './snapshot/server.min.js';

import { op_pid } from 'ext:core/ops';

globalThis.MASS = {
  _init: true,

  app: server,
  pid: op_pid,

  config: {
    port: () => 8080,
    version: () => '0.0.1',
  },
};
