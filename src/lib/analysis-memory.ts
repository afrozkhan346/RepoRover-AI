let inMemoryAnalysisBundle: unknown = null;

export function setInMemoryAnalysisBundle(bundle: unknown): void {
  inMemoryAnalysisBundle = bundle;
}

export function getInMemoryAnalysisBundle<T = unknown>(): T | null {
  return (inMemoryAnalysisBundle as T | null) ?? null;
}

export function clearInMemoryAnalysisBundle(): void {
  inMemoryAnalysisBundle = null;
}

