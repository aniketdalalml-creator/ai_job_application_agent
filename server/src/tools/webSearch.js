import { search } from "duck-duck-scrape";

/**
 * @param {string} query
 * @param {{ maxResults?: number }} [options]
 */
export async function webSearch(query, options = {}) {
  const maxResults = options.maxResults ?? 6;
  try {
    const results = await search(query, { safeSearch: 0 });
    const items = (results.results || []).slice(0, maxResults).map((item) => ({
      title: item.title || "",
      url: item.url || "",
      snippet: item.description || "",
    }));

    if (!items.length) {
      return { query, results: [], text: `No web results found for "${query}".` };
    }

    const text = items
      .map(
        (item, index) =>
          `${index + 1}. ${item.title}\n   URL: ${item.url || "n/a"}\n   ${item.snippet}`,
      )
      .join("\n\n");

    return { query, results: items, text };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { query, results: [], text: `[search error for "${query}"]: ${message}` };
  }
}

export const WEB_SEARCH_TOOL = {
  name: "web_search",
  description:
    "Search the web for recent company news, products, mission, culture, and role-relevant context.",
  input_schema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Search query, e.g. 'Stripe company products 2025'",
      },
    },
    required: ["query"],
  },
};
