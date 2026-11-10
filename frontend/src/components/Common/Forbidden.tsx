export function Forbidden() {
  return (
    <section role="alert">
      <h1 className="text-2xl font-bold">Access denied</h1>
      <p>
        You do not have permission to view this page. Contact an administrator
        if you need access.
      </p>
    </section>
  )
}
