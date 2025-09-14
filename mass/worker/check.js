if (typeof globalThis.MASS === 'undefined' || !globalThis.MASS._init) {
  throw new ReferenceError('MASS not initialized from snapshot');
}

console.log('MASS initialized from snapshot');
