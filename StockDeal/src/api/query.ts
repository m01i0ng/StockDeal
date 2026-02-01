type QueryValue = string | number | boolean | null | undefined;

export const buildQuery = (params: Record<string, QueryValue>) => {
  const entries = Object.entries(params).filter(([, value]) => value !== null && value !== undefined);
  if (entries.length === 0) {
    return "";
  }
  const searchParams = new URLSearchParams();
  for (const [key, value] of entries) {
    searchParams.set(key, String(value));
  }
  return `?${searchParams.toString()}`;
};
