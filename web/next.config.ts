import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Hides the dev-only route indicator badge (bottom-left by default) —
  // it's a debug affordance, not something we want during CRUD operations.
  // We show our own PendingOverlay (see components/ui.tsx) instead.
  devIndicators: false,
};

export default nextConfig;
