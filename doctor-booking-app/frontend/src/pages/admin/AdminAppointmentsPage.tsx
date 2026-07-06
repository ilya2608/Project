import { Card, CardContent, Container, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";
import { doctorsApi } from "../../api/doctors";
import type { AdminAppointment, Doctor } from "../../api/types";
import { formatClinicDateTime } from "../../utils/time";

export function AdminAppointmentsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctorId, setDoctorId] = useState("");
  const [appointments, setAppointments] = useState<AdminAppointment[]>([]);

  useEffect(() => {
    doctorsApi.listDoctors().then(setDoctors);
  }, []);

  useEffect(() => {
    adminApi.listAppointments(doctorId || undefined).then(setAppointments);
  }, [doctorId]);

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        All appointments
      </Typography>

      <TextField
        select
        label="Doctor"
        value={doctorId}
        onChange={(e) => setDoctorId(e.target.value)}
        sx={{ minWidth: 240, mb: 3 }}
      >
        <MenuItem value="">All doctors</MenuItem>
        {doctors.map((d) => (
          <MenuItem key={d.id} value={d.id}>
            {d.full_name}
          </MenuItem>
        ))}
      </TextField>

      <Stack spacing={1}>
        {appointments.map((a) => (
          <Card key={a.id} variant="outlined">
            <CardContent sx={{ display: "flex", justifyContent: "space-between" }}>
              <Typography>{formatClinicDateTime(a.start_at)}</Typography>
              <Typography>{a.doctor_name}</Typography>
              <Typography>{a.patient_name}</Typography>
              <Typography color="text.secondary">{a.status}</Typography>
            </CardContent>
          </Card>
        ))}
        {appointments.length === 0 && <Typography color="text.secondary">No appointments found.</Typography>}
      </Stack>
    </Container>
  );
}
