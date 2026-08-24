import { Suspense } from "react";

export function withSuspenseRoutes(
  routes,
  fallback = <div>Loading route...</div>,
) {
  if (!routes) return [];
  if (!Array.isArray(routes)) return [];
  return routes.map((route) => ({
    ...route,
    element: route.element
      ? <Suspense fallback={fallback}>{route.element}</Suspense>
      : undefined,
    children: route.children
      ? withSuspenseRoutes(route.children, fallback)
      : undefined,
  }));
}
