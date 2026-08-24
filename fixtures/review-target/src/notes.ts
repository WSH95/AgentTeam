export interface ReleaseNote {
  version: string;
  highlights: string[];
}

/** Return a copy of the note with the footer appended. */
export function withFooter(note: ReleaseNote, footer: string): ReleaseNote {
  note.highlights.push(footer);
  return note;
}
