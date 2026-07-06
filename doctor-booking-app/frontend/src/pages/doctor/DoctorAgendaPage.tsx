import { Container, Typography } from "@mui/material";
import { addDays, format } from "date-fns";
import { useEffect, useState } from "react";
import { appointmentsApi } from "../../api/appointments";
import type { Appointment } from "../../api/types";
import { WeekAgendaView } from "../../components/WeekAgendaView";

export function DoctorAgendaPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  const load = () => {
    const from = format(new Date(), "yyyy-MM-dd");
    const to = format(addDays(new Date(), 13), "yyyy-MM-dd");
    appointmentsApi.doctorAgenda(from, to).then(setAppointments);
  };

  useEffect(() => {
    load();
  }, []);

  const handleCancel = async (id: string) => {
    await appointmentsApi.cancel(id);
    load();
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        My agenda (next two weeks)
      </Typography>
      <WeekAgendaView appointments={appointments} onCancel={handleCancel} />
    </Container>
  );
}
