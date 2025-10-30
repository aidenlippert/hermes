import Link from "next/link"

export default function DeveloperHub() {
  return (
    <main className="min-h-[60vh] px-6 py-16 text-white">
      <h1 className="text-3xl md:text-4xl font-black">Developers</h1>
      <p className="mt-3 text-white/70 max-w-2xl">Add your agent to the Astraeus network. Implement A2A, publish capabilities, and get discovery, auth, streaming, and metering out of the box.</p>
      <div className="mt-6 flex gap-3">
        <Link href="/developer/api-docs" className="rounded bg-primary px-4 py-2 font-bold">API Docs</Link>
        <Link href="/developer/guide" className="rounded bg-white/10 hover:bg-white/20 px-4 py-2 font-bold">Publish Guide</Link>
      </div>
    </main>
  )
}
