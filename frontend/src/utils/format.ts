export function formatStep(step: number): string {
  return new Intl.NumberFormat("en-US").format(step);
}
