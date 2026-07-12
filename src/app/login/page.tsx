"use client";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <h1 className="text-2xl font-bold text-center mb-6">TransitOps</h1>
        <p className="text-gray-600 text-center mb-4">
          Backend is running on FastAPI at port 8000
        </p>
        <p className="text-sm text-gray-500 text-center">
          The frontend (React + Vite) needs to be set up separately as per your requirements.
        </p>
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm font-medium text-blue-900">API Documentation:</p>
          <a href="http://localhost:8000/docs" target="_blank" className="text-blue-600 hover:underline">
            http://localhost:8000/docs
          </a>
        </div>
      </div>
    </div>
  );
}
