import { Card, CardActionArea, CardContent, Container, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { doctorsApi } from "../../api/doctors";
import type { Doctor, Specialty } from "../../api/types";

export function DoctorListPage() {
  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [specialtyId, setSpecialtyId] = useState<string>("");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    doctorsApi.listSpecialties().then(setSpecialties);
  }, []);

  useEffect(() => {
    doctorsApi.listDoctors(specialtyId || undefined).then(setDoctors);
  }, [specialtyId]);

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Find a doctor
      </Typography>

      <TextField
        select
        label="Specialty"
        value={specialtyId}
        onChange={(e) => setSpecialtyId(e.target.value)}
        sx={{ minWidth: 240, mb: 3 }}
      >
        <MenuItem value="">All specialties</MenuItem>
        {specialties.map((s) => (
          <MenuItem key={s.id} value={s.id}>
            {s.name}
          </MenuItem>
        ))}
      </TextField>

      <Stack spacing={2}>
        {doctors.map((doctor) => (
          <Card key={doctor.id}>
            <CardActionArea onClick={() => navigate(`/patient/doctors/${doctor.id}`)}>
              <CardContent>
                <Typography variant="h6">{doctor.full_name}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {doctor.specialty?.name ?? "General"}
                </Typography>
                {doctor.bio && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {doctor.bio}
                  </Typography>
                )}
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
        {doctors.length === 0 && <Typography color="text.secondary">No doctors found.</Typography>}
      </Stack>
    </Container>
  );
}
