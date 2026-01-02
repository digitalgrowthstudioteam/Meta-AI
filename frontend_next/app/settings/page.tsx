// frontend_next/app/settings/page.tsx

export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">
        Settings
      </h1>
      <p className="text-sm text-gray-500">
        Account configuration and Meta connection details.
      </p>

      <div className="mt-6 bg-white border border-gray-200 rounded p-6 text-sm text-gray-600">
        This section will manage:
        <ul className="list-disc ml-5 mt-2 space-y-1">
          <li>Connected Meta ad accounts</li>
          <li>Session & login security</li>
          <li>Subscription plan details</li>
          <li>Timezone & reporting preferences</li>
        </ul>

        <div className="mt-4 text-xs text-gray-400">
          Critical changes require explicit confirmation.
        </div>
      </div>
    </div>
  );
}
