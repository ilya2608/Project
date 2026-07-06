import { Button, Card, CardContent, Stack, Typography } from "@mui/material";
import type { Appointment } from "../api/types";
import { clinicDateKey, formatClinicDayHeading, formatClinicTime } from "../utils/time";

interface WeekAgendaViewProps {
  appointments: Appointment[];
  onCancel: (id: string) => void;
}

export function WeekAgendaView({ appointments, onCancel }: WeekAgendaViewProps) {
  const byDay = new Map<string, Appointment[]>();
  for (const appt of appointments) {
    const day = clinicDateKey(appt.start_at);
    if (!byDay.has(day)) byDay.set(day, []);
    byDay.get(day)!.push(appt);
  }

  const days = [...byDay.keys()].sort();

  if (days.length === 0) {
    return <Typography color="text.secondary">No appointments in this range.</Typography>;
  }

  return (
    <Stack spacing={3}>
      {days.map((day) => (
        <div key={day}>
          <Typography variant="subtitle1" gutterBottom>
            {formatClinicDayHeading(day)}
          </Typography>
          <Stack spacing={1}>
            {byDay.get(day)!.map((appt) => (
              <Card key={appt.id} variant="outlined">
                <CardContent sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <Typography>
                    {formatClinicTime(appt.start_at)} – {formatClinicTime(appt.end_at)}
                  </Typography>
                  <Typography color="text.secondary" sx={{ flexGrow: 1, ml: 2 }}>
                    {appt.status}
                  </Typography>
                  {appt.status === "booked" && (
                    <Button color="error" size="small" onClick={() => onCancel(appt.id)}>
                      Cancel
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </Stack>
        </div>
      ))}
    </Stack>
  );
}
