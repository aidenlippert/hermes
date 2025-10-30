"use client"

import React from "react"

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  console.error("Global client error:", error)

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background-light dark:bg-background-dark">
      <div className="max-w-xl rounded-lg bg-zinc-900/60 p-8 text-zinc-100">
        <h2 className="text-2xl font-bold mb-2">Something went wrong</h2>
        <p className="mb-4">A client-side error occurred. You can try again or report this to the dev team.</p>
        <pre className="text-xs bg-zinc-800 p-3 rounded text-red-300 overflow-x-auto">{String(error.message)}</pre>
        <div className="mt-4 flex gap-2">
          <button onClick={() => reset()} className="px-4 py-2 rounded bg-primary text-white">Try again</button>
          <button onClick={() => { navigator.clipboard?.writeText(String(error.stack || error.message)); }} className="px-4 py-2 rounded border border-zinc-700 text-zinc-200">Copy error</button>
        </div>
      </div>
    </div>
  )
}
