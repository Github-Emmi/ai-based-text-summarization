"use client";

import { useAuthStore } from "@/lib/store/auth-store";
import { UpdateProfileForm } from "@/components/profile/update-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils/format";

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="p-6 max-w-xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Profile</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage your account settings.
        </p>
      </div>

      {user && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Account info</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Email</dt>
                <dd className="font-medium">{user.email}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Member since</dt>
                <dd>{formatDate(user.created_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Status</dt>
                <dd className="text-green-600">{user.is_active ? "Active" : "Inactive"}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Update profile</CardTitle>
        </CardHeader>
        <CardContent>
          <UpdateProfileForm />
        </CardContent>
      </Card>
    </div>
  );
}
