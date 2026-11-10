import type { ReactNode } from "react"
import type { Permission } from "@/client"
import { usePermissions } from "@/hooks/usePermissions"
import { Forbidden } from "./Forbidden"

export function PermissionGuard({
  permission,
  children,
}: {
  permission: Permission
  children: ReactNode
}) {
  const { can, isPending, isError, refetch } = usePermissions()
  if (isPending) return <p role="status">Checking access…</p>
  if (isError)
    return (
      <section role="alert">
        <p>Unable to verify your access.</p>
        <button type="button" onClick={() => refetch()}>
          Try again
        </button>
      </section>
    )
  if (!can(permission)) return <Forbidden />
  return children
}
