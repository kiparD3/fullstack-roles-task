import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { type UserPublic, UsersService } from "@/client"
import AddUser from "@/components/Admin/AddUser"
import { columns, type UserTableData } from "@/components/Admin/columns"
import { DataTable } from "@/components/Common/DataTable"
import { Forbidden } from "@/components/Common/Forbidden"
import { PermissionGuard } from "@/components/Common/PermissionGuard"
import PendingUsers from "@/components/Pending/PendingUsers"
import useAuth from "@/hooks/useAuth"
import { usePermissions } from "@/hooks/usePermissions"

function getUsersQueryOptions() {
  return {
    queryFn: async () =>
      (await UsersService.readUsers({ query: { skip: 0, limit: 100 } })).data,
    queryKey: ["users"],
  }
}

export const Route = createFileRoute("/_layout/admin")({
  component: Admin,
  head: () => ({
    meta: [
      {
        title: "Admin - FastAPI Template",
      },
    ],
  }),
})

function UsersTableContent() {
  const { user: currentUser } = useAuth()
  const { can } = usePermissions()
  const {
    data: users,
    error,
    isPending,
  } = useQuery({ ...getUsersQueryOptions(), retry: false })
  if (isPending) return <PendingUsers />
  if (error instanceof AxiosError && error.response?.status === 403)
    return <Forbidden />
  if (error || !users) return <p role="alert">Unable to load users.</p>

  const tableData: UserTableData[] = users.data.map((user: UserPublic) => ({
    ...user,
    isCurrentUser: currentUser?.id === user.id,
  }))

  return (
    <DataTable
      columns={
        can("users:manage")
          ? columns
          : columns.filter((column) => column.id !== "actions")
      }
      data={tableData}
    />
  )
}

function Admin() {
  const { can } = usePermissions()
  return (
    <PermissionGuard permission="users:read">
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Users</h1>
            <p className="text-muted-foreground">
              Manage user accounts and permissions
            </p>
          </div>
          {can("users:manage") && <AddUser />}
        </div>
        <UsersTableContent />
      </div>
    </PermissionGuard>
  )
}
