"use client";
import { cn } from "@/lib/utils";
import React from "react";
import { motion, useAnimate } from "motion/react";

// Aceternity's stateful button, adapted: the tick only shows when the action succeeds (it returns anything but
// `false` and doesn't throw), and `onDone` runs once the tick has been seen.
// motion.button has its own drag and animation handlers, so the plain HTML ones are left out.
type MotionConflicts = "onClick" | "onDrag" | "onDragStart" | "onDragEnd" | "onAnimationStart" | "onAnimationEnd";

interface ButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, MotionConflicts> {
  className?: string;
  children: React.ReactNode;
  onClick: () => Promise<unknown>;
  onDone?: () => void;
}

export const StatefulButton = ({ className, children, onClick, onDone, disabled, ...props }: ButtonProps) => {
  const [scope, animate] = useAnimate();
  const [busy, setBusy] = React.useState(false);

  const show = (selector: string) => animate(selector, { width: "20px", scale: 1, display: "block" }, { duration: 0.2 });
  const hide = (selector: string) => animate(selector, { width: "0px", scale: 0, display: "none" }, { duration: 0.2 });

  const handleClick = async () => {
    setBusy(true);
    await show(".loader");
    let ok = false;
    try {
      ok = (await onClick()) !== false;
    } catch {
      ok = false;
    }
    await hide(".loader");
    if (ok) {
      await show(".check");
      await new Promise((resolve) => setTimeout(resolve, 450));
      onDone?.();
    }
    setBusy(false);
  };

  return (
    <motion.button
      layout
      ref={scope}
      disabled={disabled || busy}
      aria-busy={busy}
      className={cn(
        "flex h-12 min-w-[120px] items-center justify-center gap-2 rounded-full bg-ink px-6 font-medium text-white shadow-sm transition-[box-shadow,translate,background-color] duration-200 outline-none hover:-translate-y-0.5 hover:bg-[#262626] hover:shadow-accent-lg focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-60",
        className,
      )}
      {...props}
      onClick={handleClick}
    >
      <motion.div layout className="flex items-center gap-2">
        <Loader />
        <CheckIcon />
        <motion.span layout>{children}</motion.span>
      </motion.div>
    </motion.button>
  );
};

const Loader = () => {
  return (
    <motion.svg
      animate={{
        rotate: [0, 360],
      }}
      initial={{
        scale: 0,
        width: 0,
        display: "none",
      }}
      style={{
        scale: 0.5,
        display: "none",
      }}
      transition={{
        duration: 0.6,
        repeat: Infinity,
        ease: "linear",
      }}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="loader text-white"
      aria-hidden
    >
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M12 3a9 9 0 1 0 9 9" />
    </motion.svg>
  );
};

const CheckIcon = () => {
  return (
    <motion.svg
      initial={{
        scale: 0,
        width: 0,
        display: "none",
      }}
      style={{
        scale: 0.5,
        display: "none",
      }}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="check text-white"
      aria-hidden
    >
      <path stroke="none" d="M0 0h24v24H0z" fill="none" />
      <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" />
      <path d="M9 12l2 2l4 -4" />
    </motion.svg>
  );
};
