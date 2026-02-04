import * as React from "react"
import { Slider as RadixSlider } from "radix-ui"

import { cn } from "@/lib/utils"

function Slider({
  className,
  defaultValue,
  value,
  min = 0,
  max = 100,
  step = 1,
  onValueChange,
  ...props
}: React.ComponentProps<typeof RadixSlider.Root>) {
  return (
    <RadixSlider.Root
      data-slot="slider"
      defaultValue={defaultValue}
      value={value}
      min={min}
      max={max}
      step={step}
      onValueChange={onValueChange}
      className={cn(
        "relative flex w-full touch-none items-center select-none",
        className
      )}
      {...props}
    >
      <RadixSlider.Track className="bg-muted relative h-1.5 w-full grow overflow-hidden rounded-full">
        <RadixSlider.Range className="bg-primary absolute h-full" />
      </RadixSlider.Track>
      <RadixSlider.Thumb className="border-primary/50 bg-background focus-visible:ring-ring block size-4 rounded-full border shadow transition-colors focus-visible:ring-1 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50" />
    </RadixSlider.Root>
  )
}

export { Slider }
