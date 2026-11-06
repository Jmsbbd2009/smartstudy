import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
const variants = cva(
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default: "bg-blue text-white hover:bg-blue-600",
        outline: "border border-slate-200 bg-white text-navy hover:bg-slate-50",
        ghost: "text-slate-600 hover:bg-slate-100",
        danger: "bg-red-50 text-red-700 hover:bg-red-100",
      },
    },
    defaultVariants: { variant: "default" },
  },
);
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof variants> {
  asChild?: boolean;
}
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, asChild, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={twMerge(clsx(variants({ variant }), className))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";
