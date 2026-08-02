export const VIETNAM_TIME_ZONE = "Asia/Ho_Chi_Minh";

const VIETNAM_UTC_OFFSET = "+07:00";

const vietnamDateTimeFormatter = new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: VIETNAM_TIME_ZONE,
});

const vietnamDateFormatter = new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "medium",
  timeZone: VIETNAM_TIME_ZONE,
});

const vietnamLocalInputFormatter = new Intl.DateTimeFormat("en-CA", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
  timeZone: VIETNAM_TIME_ZONE,
});

export function parseApiDateTime(value: string): Date {
  const hasTimeZone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value);
  const parsed = new Date(hasTimeZone ? value : `${value}Z`);

  if (Number.isNaN(parsed.getTime())) {
    throw new Error(`Invalid API datetime: ${value}`);
  }

  return parsed;
}

export function createVietnamDateTimeFormatter(
  options: Intl.DateTimeFormatOptions
): Intl.DateTimeFormat {
  return new Intl.DateTimeFormat("vi-VN", {
    ...options,
    timeZone: VIETNAM_TIME_ZONE,
  });
}

export function formatVietnamDateTime(value: string): string {
  return vietnamDateTimeFormatter.format(parseApiDateTime(value));
}

export function formatVietnamDate(value: string): string {
  return vietnamDateFormatter.format(parseApiDateTime(value));
}

export function toVietnamLocalInputValue(date: Date): string {
  const parts = Object.fromEntries(
    vietnamLocalInputFormatter
      .formatToParts(date)
      .filter(({ type }) => type !== "literal")
      .map(({ type, value }) => [type, value])
  );

  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

export function vietnamLocalInputToUtcIso(value: string): string {
  const seconds = value.length === 16 ? ":00" : "";
  const parsed = new Date(`${value}${seconds}${VIETNAM_UTC_OFFSET}`);

  if (Number.isNaN(parsed.getTime())) {
    throw new Error(`Invalid Vietnam local datetime: ${value}`);
  }

  return parsed.toISOString();
}
