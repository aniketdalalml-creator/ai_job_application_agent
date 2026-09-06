export default function LoginView({
  email,
  setEmail,
  password,
  setPassword,
  submitting,
  error,
  onSubmit,
  onSwitch,
}) {
  return (
    <div className="mx-auto max-w-md space-y-8 pt-10">
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full bg-primary-fixed px-3 py-1 text-[12px] font-semibold text-primary">
          <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
          Career Copilot
        </div>
        <h2 className="text-[36px] font-bold leading-tight tracking-tight">Sign in</h2>
        <p className="text-[14px] text-on-surface-variant">
          Your profile, ranked jobs, and applications stay scoped to this account.
        </p>
      </div>
      <form onSubmit={onSubmit} className="institutional-panel space-y-5 p-8">
        <label className="block space-y-2">
          <span className="label-caps">Email</span>
          <input
            className="input-field"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            autoComplete="email"
          />
        </label>
        <label className="block space-y-2">
          <span className="label-caps">Password</span>
          <input
            className="input-field"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            autoComplete="current-password"
          />
        </label>
        {error ? <p className="text-[13px] font-medium text-error">{error}</p> : null}
        <button type="submit" className="btn-primary w-full" disabled={submitting}>
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <p className="text-center text-[13px] text-on-surface-variant">
        New here?{" "}
        <button type="button" className="font-semibold text-primary" onClick={onSwitch}>
          Create an account
        </button>
      </p>
    </div>
  );
}
