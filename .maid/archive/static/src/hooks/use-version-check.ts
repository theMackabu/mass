import useSWR from 'swr';
import { useEffect } from 'react';

type BuildInfo = { hash: string };

const fetchHash = async (url: string): Promise<BuildInfo> => {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`failed to fetch ${url}: ${response.status}`);
  }

  const data = (await response.json()) as BuildInfo;

  if (!data || typeof data.hash !== 'string') {
    throw new Error('Invalid build.json structure');
  }

  return data;
};

// make this emit "a newer version of this page is available"
export function useVersionCheck(): void {
  const isProduction = import.meta.env.PROD;
  const currentBuildHash: string = import.meta.env.VITE_BUILD_HASH;

  const { data: buildData, error } = useSWR<BuildInfo, Error>(
    isProduction ? '/build.json' : null,
    fetchHash,
    {
      refreshInterval: 5 * 60 * 1000,
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      dedupingInterval: 30 * 1000,
      shouldRetryOnError: false,
      errorRetryCount: 0,
    },
  );

  useEffect(() => {
    if (buildData?.hash && buildData.hash !== currentBuildHash) {
      console.log(`new version detected: ${currentBuildHash} -> ${buildData.hash}, reloading...`);
      window.location.reload();
    }
  }, [buildData]);

  useEffect(() => {
    if (error) console.warn('version check failed:', error.message);
  }, [error]);
}
