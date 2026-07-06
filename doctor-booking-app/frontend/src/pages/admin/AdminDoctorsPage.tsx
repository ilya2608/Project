import { Button, Card, CardActionArea, CardContent, Container, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { adminApi } from "../../api/admin";
import type { Doctor } from "../../api/types";

export function AdminDoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    adminApi.listDoctors().then(setDoctors);
  }, []);

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h5">Doctors</Typography>
        <Button variant="contained" onClick={() => navigate("/admin/doctors/new")}>
          Add doctor
        </Button>
      </Stack>

      <Stack spacing={2}>
        {doctors.map((doctor) => (
          <Card key={doctor.id}>
            <CardActionArea onClick={() => navigate(`/admin/doctors/${doctor.id}/edit`)}>
              <CardContent sx={{ display: "flex", justifyContent: "space-between" }}>
                <Typography>{doctor.full_name}</Typography>
                <Typography color="text.secondary">{doctor.specialty?.name ?? "General"}</Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Stack>
    </Container>
  );
}
