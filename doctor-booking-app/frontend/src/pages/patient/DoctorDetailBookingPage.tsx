import { Alert, Container, Paper, Snackbar, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { appointmentsApi } from "../../api/appointments";
import { doctorsApi } from "../../api/doctors";
import type { Doctor } from "../../api/types";
import { SlotPicker } from "../../components/SlotPicker";
import { formatClinicDateTime } from "../../utils/time";

export function DoctorDetailBookingPage() {
  const { doctorId } = useParams<{ doctorId: string }>();
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [confirmation, setConfirmation] = useState<string | null>(null);

  useEffect(() => {
    if (doctorId) doctorsApi.getDoctor(doctorId).then(setDoctor);
  }, [doctorId]);

  if (!doctorId) return null;

  const handleBook = async (startAtIso: string) => {
    await appointmentsApi.book(doctorId, startAtIso);
    setConfirmation(`Booked! See you at ${formatClinicDateTime(startAtIso)}.`);
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      {doctor && (
        <>
          <Typography variant="h5">{doctor.full_name}</Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {doctor.specialty?.name ?? "General"}
          </Typography>
        </>
      )}

      <Paper sx={{ p: 3, mt: 2 }}>
        {doctor && !doctor.is_accepting_bookings ? (
          <Alert severity="info">This doctor is not accepting new bookings right now.</Alert>
        ) : (
          <SlotPicker doctorId={doctorId} onBook={handleBook} />
        )}
      </Paper>

      <Snackbar
        open={confirmation !== null}
        autoHideDuration={5000}
        onClose={() => setConfirmation(null)}
        message={confirmation}
      />
    </Container>
  );
}
