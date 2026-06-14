import type { PropsWithChildren } from "react";

export function AppProviders({ children }: PropsWithChildren) {
  // Shared providers (query cache, theme, routing) will be composed here.
  return children;
}
