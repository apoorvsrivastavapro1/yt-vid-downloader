import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost";
  size?: "default" | "sm" | "lg";
};

const sizeClasses = {
  default: "h-10 px-4 py-2",
  sm: "h-8 px-3 text-sm",
  lg: "h-12 px-6 text-base",
};

export function Button({
  variant = "default",
  size = "default",
  className = "",
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-lg font-medium transition-colors disabled:pointer-events-none disabled:opacity-50";
  const variants = {
    default: "bg-foreground text-background hover:bg-foreground/90",
    ghost: "hover:bg-muted text-foreground",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    />
  );
}
