"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import axios from "axios";

import { loginSchema, type LoginFormValues } from "@/lib/utils/validators";
import { login } from "@/lib/api/auth";
import { getMe } from "@/lib/api/users";
import { useAuthStore } from "@/lib/store/auth-store";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(values: LoginFormValues) {
    try {
      const tokens = await login(values);

      // Persist refresh token in httpOnly cookie
      await fetch("/api/auth/set-cookie", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: tokens.refresh_token }),
      });

      // Fetch user profile
      // Temporarily set token so the API client can use it
      useAuthStore.getState().setAccessToken(tokens.access_token);
      const user = await getMe();

      setAuth(tokens.access_token, user);
      router.push("/summarize");
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        toast.error("Invalid email or password");
      } else {
        toast.error("Login failed. Please try again.");
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">Sign in</CardTitle>
        <CardDescription>Enter your email and password to continue.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              {...register("email")}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register("password")}
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-primary hover:underline">
            Create one
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
