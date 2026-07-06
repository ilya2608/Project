import {
  Alert,
  Button,
  Checkbox,
  Container,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { adminApi } from "../../api/admin";
import { ApiError } from "../../api/client";
import { doctorsApi } from "../../api/doctors";
import type { Specialty } from "../../api/types";

export function AdminDoctorFormPage() {
  const { doctorId } = useParams<{ doctorId: string }>();
  const isEdit = Boolean(doctorId);
  const navigate = useNavigate();

  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [specialtyId, setSpecialtyId] = useState("");
  const [bio, setBio] = useState("");
  const [slotDuration, setSlotDuration] = useState(30);
  const [isAcceptingBookings, setIsAcceptingBookings] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    doctorsApi.listSpecialties().then(setSpecialties);
  }, []);

  useEffect(() => {
    if (doctorId) {
      doctorsApi.getDoctor(doctorId).then((doctor) => {
        setFullName(doctor.full_name);
        setSpecialtyId(doctor.specialty?.id ?? "");
        setBio(doctor.bio ?? "");
        setSlotDuration(doctor.slot_duration_minutes);
        setIsAcceptingBookings(doctor.is_accepting_bookings);
      });
    }
  }, [doctorId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (isEdit && doctorId) {
        await adminApi.updateDoctor(doctorId, {
          full_name: fullName,
          specialty_id: specialtyId || undefined,
          bio,
          slot_duration_minutes: slotDuration,
          is_accepting_bookings: isAcceptingBookings,
        });
      } else {
        await adminApi.createDoctor({
          email,
          full_name: fullName,
          password,
          specialty_id: specialtyId || undefined,
          bio,
          slot_duration_minutes: slotDuration,
        });
      }
      navigate("/admin/doctors");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save doctor");
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h5" gutterBottom>
          {isEdit ? "Edit doctor" : "Add doctor"}
        </Typography>
        <form onSubmit={handleSubmit}>
          <Stack spacing={2}>
            {error && <Alert severity="error">{error}</Alert>}
            {!isEdit && (
              <>
                <TextField
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                <TextField
                  label="Temporary password"
                  type="text"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  helperText="Share this with the doctor so they can log in and change it."
                />
              </>
            )}
            <TextField label="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            <TextField
              select
              label="Specialty"
              value={specialtyId}
              onChange={(e) => setSpecialtyId(e.target.value)}
            >
              <MenuItem value="">None</MenuItem>
              {specialties.map((s) => (
                <MenuItem key={s.id} value={s.id}>
                  {s.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Bio" value={bio} onChange={(e) => setBio(e.target.value)} multiline rows={3} />
            <TextField
              label="Appointment length (minutes)"
              type="number"
              value={slotDuration}
              onChange={(e) => setSlotDuration(Number(e.target.value))}
            />
            {isEdit && (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={isAcceptingBookings}
                    onChange={(e) => setIsAcceptingBookings(e.target.checked)}
                  />
                }
                label="Accepting bookings"
              />
            )}
            <Button type="submit" variant="contained">
              Save
            </Button>
          </Stack>
        </form>
      </Paper>
    </Container>
  );
}
