import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { MetricsService } from "@/client"
import { Forbidden } from "@/components/Common/Forbidden"
import { PermissionGuard } from "@/components/Common/PermissionGuard"

export const Route = createFileRoute("/_layout/metrics")({ component: Metrics })

function MetricsContent() {
  const { data, error, isPending } = useQuery({
    queryKey: ["metrics"],
    queryFn: async () => (await MetricsService.readMetrics()).data,
    retry: false,
  })
  if (isPending) return <p role="status">Loading metrics…</p>
  if (error instanceof AxiosError && error.response?.status === 403)
    return <Forbidden />
  if (error || !data) return <p role="alert">Unable to load metrics.</p>
  return (
    <section>
      <h1 className="text-2xl font-bold">Metrics</h1>
      <p>{data.message}</p>
      <p>Active projects: {data.active_projects}</p>
      <p className="text-muted-foreground">
        Sample data for the authorization demonstration.
      </p>
    </section>
  )
}

function Metrics() {
  return (
    <PermissionGuard permission="metrics:read">
      <MetricsContent />
    </PermissionGuard>
  )
}
