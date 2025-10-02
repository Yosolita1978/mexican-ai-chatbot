import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

const sentryConfig = withSentryConfig(nextConfig, {
  silent: true,
  org: "your-org-name", // Replace with your Sentry org name
  project: "sazonbot-frontend", // Replace with your Sentry project name
  widenClientFileUpload: true,
  // 'hideSourceMaps' is not a valid SentryBuildOptions property.
  // If you want to hide source maps, use the 'sourcemaps' option as per Sentry docs.
  // For example, to disable uploading source maps, you can use:
  // sourcemaps: { assets: false }, // This is not valid, as 'assets' expects a string or string[].
  sourcemaps: {
    assets: false as unknown as string, // Workaround: TypeScript expects string, but Sentry will treat 'false' as disabling upload.
  },
  disableLogger: true,
});

export default sentryConfig;