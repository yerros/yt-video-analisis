'use client'

export default function Error({
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h2 className="text-2xl font-bold mb-4">Terjadi kesalahan</h2>
      <p className="text-gray-600 mb-4">Maaf, terjadi kesalahan saat memuat halaman.</p>
      <button
        onClick={reset}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Coba lagi
      </button>
    </div>
  )
}
