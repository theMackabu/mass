interface OPS_CONFIG {
  port(): number;
  version(): string;
}

interface OPS_MASS {
  _init: boolean;
  pid(): number;
  config: OPS_CONFIG;
}

declare global {
  const MASS: OPS_MASS;
}

export {};
