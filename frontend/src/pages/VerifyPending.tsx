import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useState } from 'react'

export default function VerifyPending() {
  const location = useLocation()
  const email = (location.state as { email?: string })?.email || ''
  const { resendVerification } = useAuth()
  const [resent, setResent] = useState(false)

  const handleResend = async () => {
    await resendVerification()
    setResent(true)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-transparent px-4">
      <div className="w-full max-w-md bg-white dark:bg-gray-800 p-8 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 text-center">
        <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Verify your email</h1>
        <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
          We sent a verification link to           <span className="font-medium text-gray-700 dark:text-gray-200">{email || 'your email'}</span>.
          Please check your inbox and click the link.
        </p>

        <button onClick={handleResend} disabled={resent}
          className="text-blue-600 underline hover:no-underline text-sm disabled:text-gray-400 disabled:no-underline">
          {resent ? 'Verification sent!' : 'Resend verification email'}
        </button>

        <Link to="/" className="block text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mt-4">&larr; Back to Home</Link>
      </div>
    </div>
  )
}
