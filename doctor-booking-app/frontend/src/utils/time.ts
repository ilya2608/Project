// The clinic operates in a fixed timezone regardless of the patient's or
// doctor's browser locale — a slot at "09:00" always means 09:00 in
// Brussels. Formatting with the browser's local timezone (e.g. a patient
// visiting from a UTC or US timezone) would silently show the wrong wall-
// clock time, so every appointment/slot time in the UI must go through
// these helpers instead of raw Date/toLocaleString formatting.
const CLINIC_TIMEZONE = "Europe/Brussels";

export function formatClinicTime(isoString: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: CLINIC_TIMEZONE,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(isoString));
}

export function formatClinicDateTime(isoString: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: CLINIC_TIMEZONE,
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(isoString));
}

export function clinicDateKey(isoString: string): string {
  // en-CA gives YYYY-MM-DD directly, handy as a sortable grouping key.
  return new Intl.DateTimeFormat("en-CA", { timeZone: CLINIC_TIMEZONE }).format(new Date(isoString));
}

export function formatClinicDayHeading(isoDateString: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: CLINIC_TIMEZONE,
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date(`${isoDateString}T12:00:00Z`));
}
