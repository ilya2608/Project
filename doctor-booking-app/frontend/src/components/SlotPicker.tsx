import { Alert, Box, Button, Chip, Stack, TextField, Typography } from "@mui/material";
import { addDays, format } from "date-fns";
import { useEffect, useState } from "react";
import { doctorsApi } from "../api/doctors";
import { ApiError } from "../api/client";
import type { Slot } from "../api/types";
import { formatClinicTime } from "../utils/time";

interface SlotPickerProps {
  doctorId: string;
  onBook: (startAtIso: string) => Promise<void>;
}

const DATE_FMT = "yyyy-MM-dd";

export function SlotPicker({ doctorId, onBook }: SlotPickerProps) {
  const [selectedDate, setSelectedDate] = useState(() => format(new Date(), DATE_FMT));
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    doctorsApi
      .getSlots(doctorId, selectedDate, selectedDate)
      .then((byDate) => setSlots(byDate[0]?.slots ?? []))
      .catch(() => setError("Could not load available slots."))
      .finally(() => setLoading(false));
  }, [doctorId, selectedDate]);

  const shiftDate = (days: number) => {
    setSelectedDate((d) => format(addDays(new Date(d), days), DATE_FMT));
  };

  const handleBook = async (slot: Slot) => {
    setBooking(slot.start_at);
    setError(null);
    try {
      await onBook(slot.start_at);
      setSlots((prev) => prev.filter((s) => s.start_at !== slot.start_at));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not book this slot.");
    } finally {
      setBooking(null);
    }
  };

  return (
    <Box>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
        <Button onClick={() => shiftDate(-1)}>&larr; Previous day</Button>
        <TextField
          type="date"
          size="small"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        />
        <Button onClick={() => shiftDate(1)}>Next day &rarr;</Button>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Typography color="text.secondary">Loading available times…</Typography>
      ) : slots.length === 0 ? (
        <Typography color="text.secondary">No available times on this day.</Typography>
      ) : (
        <Stack direction="row" flexWrap="wrap" gap={1}>
          {slots.map((slot) => (
            <Chip
              key={slot.start_at}
              label={formatClinicTime(slot.start_at)}
              color="primary"
              variant={booking === slot.start_at ? "filled" : "outlined"}
              clickable
              disabled={booking !== null}
              onClick={() => handleBook(slot)}
            />
          ))}
        </Stack>
      )}
    </Box>
  );
}
