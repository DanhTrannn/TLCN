export const STAFF_ROLES = [
  "admin",
  "store_manager",
  "sales_manager",
  "marketing_manager",
  "inventory_manager",
  "operations_manager",
  "system_admin",
] as const;

export type StaffRole = (typeof STAFF_ROLES)[number];

export function isStaffRole(role?: string | null): role is StaffRole {
  return typeof role === "string" && STAFF_ROLES.includes(role as StaffRole);
}

export function getRoleHomeRoute(role?: string | null): string {
  switch (role) {
    case "admin":
      return "/admin";
    case "store_manager":
      return "/store";
    case "sales_manager":
      return "/admin/analytics?role=sales";
    case "marketing_manager":
      return "/admin/analytics?role=marketing";
    case "inventory_manager":
      return "/admin/inbound";
    case "operations_manager":
      return "/admin/analytics?role=operations";
    case "system_admin":
      return "/admin/analytics?role=system";
    default:
      return "/products";
  }
}

export function getRoleLabel(role?: string | null): string {
  switch (role) {
    case "admin":
      return "Tổng quan Quản trị";
    case "store_manager":
      return "Quản lý Cửa hàng";
    case "sales_manager":
      return "Báo cáo Kinh doanh";
    case "marketing_manager":
      return "Báo cáo Marketing";
    case "inventory_manager":
      return "Nhập kho sản xuất & COGS";
    case "operations_manager":
      return "Báo cáo Vận hành";
    case "system_admin":
      return "Kỹ thuật & Đối soát";
    case "customer":
      return "Cửa hàng thời trang";
    default:
      return "Khu vực làm việc";
  }
}

export function canRoleAccessRoute(role: string | null | undefined, rawPath: string): boolean {
  const path = rawPath.split("?")[0];

  // Customer public routes accessible to everyone
  const publicPrefixes = [
    "/products",
    "/cart",
    "/checkout",
    "/orders",
    "/wishlist",
    "/login",
    "/register",
  ];
  if (path === "/" || publicPrefixes.some((prefix) => path === prefix || path.startsWith(`${prefix}/`))) {
    return true;
  }

  // Admin has access to everything
  if (role === "admin") {
    return true;
  }

  // Store area
  if (path === "/store" || path.startsWith("/store/")) {
    return role === "store_manager";
  }

  // Analytics hub accessible by all staff roles (fine-grained tab RBAC handled inside component)
  if (path === "/admin/analytics" || path.startsWith("/admin/analytics/")) {
    return isStaffRole(role);
  }

  // Role-specific operational admin routes
  if (role === "inventory_manager") {
    return (
      path.startsWith("/admin/inbound") ||
      path.startsWith("/admin/products")
    );
  }

  if (role === "operations_manager") {
    return (
      path.startsWith("/admin/orders") ||
      path.startsWith("/admin/returns") ||
      path.startsWith("/admin/logistics")
    );
  }

  if (role === "marketing_manager") {
    return (
      path.startsWith("/admin/coupons") ||
      path.startsWith("/admin/reviews")
    );
  }

  // /admin root overview or unauthorized admin subpages are restricted to admin
  return false;
}

export function resolvePostLoginRedirect(
  role: string | null | undefined,
  requestedReturnTo: string | null
): string {
  if (!requestedReturnTo || requestedReturnTo === "/" || requestedReturnTo === "/products") {
    return getRoleHomeRoute(role);
  }

  // Protect against open redirect attacks
  if (!requestedReturnTo.startsWith("/") || requestedReturnTo.startsWith("//")) {
    return getRoleHomeRoute(role);
  }

  if (canRoleAccessRoute(role, requestedReturnTo)) {
    return requestedReturnTo;
  }

  return getRoleHomeRoute(role);
}
