import { z } from "zod";

const PASSWORD_REGEX = /^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$/;
const PASSWORD_MESSAGE =
  "Password must be 8–128 characters and include at least one uppercase letter, one number, and one special character (@$!%*?&).";

const strongPassword = z.string().regex(PASSWORD_REGEX, PASSWORD_MESSAGE);

export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = z
  .object({
    email: z.string().email("Invalid email address"),
    password: strongPassword,
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export const updateProfileSchema = z
  .object({
    email: z.string().email("Invalid email address").optional().or(z.literal("")),
    password: strongPassword.optional().or(z.literal("")),
    confirmPassword: z.string().optional().or(z.literal("")),
  })
  .refine(
    (data) => {
      if (data.password && data.password !== data.confirmPassword) return false;
      return true;
    },
    { message: "Passwords do not match", path: ["confirmPassword"] }
  );

export const summarizeTextSchema = z.object({
  text: z.string().min(50, "Text must be at least 50 characters"),
  format: z.enum(["paragraph", "bullets"]).optional(),
  summary_length: z.enum(["short", "medium", "long"]).optional(),
});

export type LoginFormValues = z.infer<typeof loginSchema>;
export type RegisterFormValues = z.infer<typeof registerSchema>;
export type UpdateProfileFormValues = z.infer<typeof updateProfileSchema>;
export type SummarizeTextFormValues = z.infer<typeof summarizeTextSchema>;
