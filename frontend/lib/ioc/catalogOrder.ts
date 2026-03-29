/** Must match backend ``CATALOG_ORDER`` ids (spec §4.4). */
export const SOURCE_CATALOG_IDS = [
  "misp",
  "virustotal",
  "abuseipdb",
  "otx",
  "shodan",
  "urlscan",
  "malwarebazaar",
  "threatfox",
  "safebrowsing",
  "greynoise",
  "ibm_xforce",
] as const;

export type SourceCatalogId = (typeof SOURCE_CATALOG_IDS)[number];
