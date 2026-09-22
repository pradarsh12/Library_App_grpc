import { LinkButton } from "./ui";

/**
 * Reads the `page`/`prev` query params a list page's searchParams carry.
 * `page` is the opaque token for the page currently shown; `prev` is the
 * comma-joined stack of tokens visited to get here, oldest first — needed
 * because PageResponse only hands back a *forward* cursor (next_page_token),
 * so a working "Previous" link has to remember where it's been itself.
 */
export function parsePagination(searchParams: {
  page?: string | string[];
  prev?: string | string[];
}): { pageToken: string; prevTokens: string[] } {
  const pageToken = typeof searchParams.page === "string" ? searchParams.page : "";
  // The stack can legitimately contain a single "" entry (the token for
  // page 1, pushed when navigating from page 1 to page 2), which encodes
  // as a present-but-empty `prev=` param — so presence (`typeof === "string"`)
  // is what's checked here, not truthiness. "".split(",") correctly yields
  // [""] rather than [], keeping this symmetric with how hrefFor encodes it.
  const prevTokens =
    typeof searchParams.prev === "string" ? searchParams.prev.split(",") : [];
  return { pageToken, prevTokens };
}

/**
 * Previous/Next controls for a cursor-paginated list. `params` are the
 * page's other query params (search text, filters) to carry along so
 * paging doesn't reset them.
 */
export function Pagination({
  basePath,
  params,
  pageToken,
  prevTokens,
  nextPageToken,
}: {
  basePath: string;
  params: Record<string, string | undefined>;
  pageToken: string;
  prevTokens: string[];
  nextPageToken: string;
}) {
  const hasPrev = prevTokens.length > 0;
  const hasNext = nextPageToken.length > 0;
  if (!hasPrev && !hasNext) return null;

  function hrefFor(token: string, stack: string[]): string {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value) query.set(key, value);
    }
    if (token) query.set("page", token);
    if (stack.length > 0) query.set("prev", stack.join(","));
    const qs = query.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  }

  const prevHref = hasPrev
    ? hrefFor(prevTokens[prevTokens.length - 1], prevTokens.slice(0, -1))
    : undefined;
  const nextHref = hasNext ? hrefFor(nextPageToken, [...prevTokens, pageToken]) : undefined;

  return (
    <div className="mt-4 flex items-center justify-between">
      {prevHref ? <LinkButton href={prevHref}>Previous</LinkButton> : <span />}
      {nextHref ? <LinkButton href={nextHref}>Next</LinkButton> : <span />}
    </div>
  );
}
