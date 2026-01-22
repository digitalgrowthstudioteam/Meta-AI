"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

export default function UserUsageOverridePage({ params }: { params: { id: string } }) {
  const userId = params.id;
  const router = useRouter();

  const [campaignLimit, setCampaignLimit] = useState<number | null>(null);
  const [adLimit, setAdLimit] = useState<number | null>(null);
  const [expiry, setExpiry] = useState<string>("");

  const [loading, setLoading] = useState(true);

  // =========================
  // LOAD EXISTING OVERRIDE
  // =========================
  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`/api/admin/users/${userId}/usage`, {
          method: "GET",
          credentials: "include",
        });

        if (!res.ok) {
          toast.error("Failed to load usage overrides");
          setLoading(false);
          return;
        }

        const data = await res.json();

        // data is array of overrides
        const campaigns = data.find((x: any) => x.key === "campaigns");
        const adAccounts = data.find((x: any) => x.key === "ad_accounts");

        if (campaigns) {
          setCampaignLimit(campaigns.value);
          if (campaigns.expires_at) {
            setExpiry(campaigns.expires_at.split("T")[0]);
          }
        }

        if (adAccounts) {
          setAdLimit(adAccounts.value);
          // expiry is shared; use whichever has value
          if (!expiry && adAccounts.expires_at) {
            setExpiry(adAccounts.expires_at.split("T")[0]);
          }
        }
      } catch (err) {
        console.error(err);
        toast.error("Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [userId]);

  // =========================
  // SAVE LOGIC
  // =========================
  const onSave = async () => {
    try {
      // DELETE when empty
      if (campaignLimit === null) {
        await fetch(`/api/admin/users/${userId}/usage`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            key: "campaigns",
            reason: "Manual reset via UI",
          }),
        });
      } else {
        await fetch(`/api/admin/users/${userId}/usage`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            key: "campaigns",
            value: campaignLimit,
            expires_at: expiry ? new Date(expiry).toISOString() : null,
            reason: "Manual override via UI",
          }),
        });
      }

      if (adLimit === null) {
        await fetch(`/api/admin/users/${userId}/usage`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            key: "ad_accounts",
            reason: "Manual reset via UI",
          }),
        });
      } else {
        await fetch(`/api/admin/users/${userId}/usage`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            key: "ad_accounts",
            value: adLimit,
            expires_at: expiry ? new Date(expiry).toISOString() : null,
            reason: "Manual override via UI",
          }),
        });
      }

      toast.success("Override saved successfully");
      router.back();
    } catch (err) {
      console.error(err);
      toast.error("Failed to save override");
    }
  };

  if (loading) {
    return <div className="p-4">Loading usage overrides...</div>;
  }

  return (
    <div className="space-y-6 p-4 max-w-lg">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Usage Override</h1>
        <p className="text-sm text-gray-500">
          Manually override usage limits for this user
        </p>
        <div className="text-xs text-gray-400 mt-1">
          User ID: {userId}
        </div>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-sm mb-1 font-medium text-gray-700">
            Campaign Limit Override
          </label>
          <input
            type="number"
            value={campaignLimit ?? ""}
            onChange={(e) =>
              setCampaignLimit(e.target.value ? Number(e.target.value) : null)
            }
            placeholder="Leave blank to remove override"
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm mb-1 font-medium text-gray-700">
            Ad Account Limit Override
          </label>
          <input
            type="number"
            value={adLimit ?? ""}
            onChange={(e) =>
              setAdLimit(e.target.value ? Number(e.target.value) : null)
            }
            placeholder="Leave blank to remove override"
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm mb-1 font-medium text-gray-700">
            Override Expiry (optional)
          </label>
          <input
            type="date"
            value={expiry}
            onChange={(e) => setExpiry(e.target.value)}
            className="w-full border rounded px-3 py-2 text-sm"
          />
        </div>
      </div>

      <button
        onClick={onSave}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-indigo-500"
      >
        Save Override
      </button>
    </div>
  );
}
