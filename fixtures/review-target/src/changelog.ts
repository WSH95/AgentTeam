/** Return the first `count` changelog entries in file order. */
export function firstEntries(lines: string[], count: number): string[] {
  const selected: string[] = [];
  for (let i = 0; i <= count; i++) {
    selected.push(lines[i]);
  }
  return selected;
}
