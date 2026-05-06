"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import axios from "axios";

import { updateProfileSchema, type UpdateProfileFormValues } from "@/lib/utils/validators";
import { updateMe } from "@/lib/api/users";
import { useAuthStore } from "@/lib/store/auth-store";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export function UpdateProfileForm() {
  const { user, setUser } = useAuthStore();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UpdateProfileFormValues>({
    resolver: zodResolver(updateProfileSchema),
    defaultValues: { email: user?.email ?? "" },
  });

  async function onSubmit(values: UpdateProfileFormValues) {
    const payload: { email?: string; password?: string } = {};
    if (values.email && values.email !== user?.email) payload.email = values.email;
    if (values.password) payload.password = values.password;

    if (Object.keys(payload).length === 0) {
      toast.info("No changes to save");
      return;
    }

    try {
      const updated = await updateMe(payload);
      setUser(updated);
      reset({ email: updated.email, password: "", confirmPassword: "" });
      toast.success("Profile updated");
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        toast.error("That email is already in use.");
      } else {
        toast.error("Update failed. Please try again.");
      }
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div className="space-y-1.5">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          autoComplete="email"
          {...register("email")}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <Separator />

      <p className="text-xs text-muted-foreground">
        Leave password fields blank to keep your current password.
      </p>

      <div className="space-y-1.5">
        <Label htmlFor="password">New password</Label>
        <Input
          id="password"
          type="password"
          autoComplete="new-password"
          placeholder="Min. 8 characters"
          {...register("password")}
        />
        {errors.password && (
          <p className="text-sm text-destructive">{errors.password.message}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirmPassword">Confirm new password</Label>
        <Input
          id="confirmPassword"
          type="password"
          autoComplete="new-password"
          {...register("confirmPassword")}
        />
        {errors.confirmPassword && (
          <p className="text-sm text-destructive">
            {errors.confirmPassword.message}
          </p>
        )}
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : "Save changes"}
      </Button>
    </form>
  );
}
