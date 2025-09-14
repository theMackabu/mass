import server from './snapshot/server.min.js';

import {
  op_pid,
  op_extract_tar_gz,
  op_analyze_repository,
  op_get_important_files,
  op_get_important_files_by_pattern,
  op_cleanup_temp_directory,
} from 'ext:core/ops';

globalThis.MASS = {
  _init: true,

  app: server,
  pid: op_pid,

  ops: {
    op_extract_tar_gz,
    op_analyze_repository,
    op_get_important_files,
    op_get_important_files_by_pattern,
    op_cleanup_temp_directory,
  },

  config: {
    port: () => 8080,
    version: () => '0.0.1',
  },
};
