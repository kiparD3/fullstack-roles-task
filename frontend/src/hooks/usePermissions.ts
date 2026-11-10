import type { Permission } from "@/client"
import useAuth from "./useAuth"

export function usePermissions() {
  const { user, isPending, isError, refetch } = useAuth()
  return {
    can: (permission: Permission) =>
      !isPending && !isError && !!user?.capabilities.includes(permission),
    isPending,
    isError,
    refetch,
  }
}
