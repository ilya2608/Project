import { Button, Card, CardContent, Chip, Container, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { appointmentsApi } from "../../api/appointments";
import type { Appointment } from "../../api/types";
import { formatClinicDateTime } from "../../utils/time";

export function MyAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  const load = () => appointmentsApi.mine().then(setAppointments);

  useEffect(() => {
    load();
  }, []);

  const handleCancel = async (id: string) => {
    await appointmentsApi.cancel(id);
    load();
  };

  const upcoming = appointments.filter((a) => a.status === "booked");
  const past = appointments.filter((a) => a.status !== "booked");

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        My appointments
      </Typography>

      <Typography variant="subtitle1" sx={{ mt: 2 }}>
        Upcoming
      </Typography>
      <Stack spacing={2} sx={{ mb: 4 }}>
        {upcoming.length === 0 && <Typography color="text.secondary">No upcoming appointments.</Typography>}
        {upcoming.map((a) => (
          <Card key={a.id}>
            <CardContent sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Typography>{formatClinicDateTime(a.start_at)}</Typography>
              <Button color="error" onClick={() => handleCancel(a.id)}>
                Cancel
              </Button>
            </CardContent>
          </Card>
        ))}
      </Stack>

      <Typography variant="subtitle1">Past</Typography>
      <Stack spacing={2}>
        {past.map((a) => (
          <Card key={a.id} variant="outlined">
            <CardContent sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Typography color="text.secondary">{formatClinicDateTime(a.start_at)}</Typography>
              <Chip label={a.status.replaceAll("_", " ")} size="small" />
            </CardContent>
          </Card>
        ))}
      </Stack>
    </Container>
  );
}
